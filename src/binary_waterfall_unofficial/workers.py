from __future__ import annotations

import os
import math
import wave
import shutil

from PySide6.QtCore import QThread, Signal, QMutex
from PySide6.QtGui import QImage

from . import generators, constants
from .lang import L


class FileWorker(QThread):
    """Background worker for file opening and mmap loading."""
    
    progress = Signal(int, str)  # (percentage, status text)
    finished = Signal(dict)      # {filename, total_bytes, audio_filename}
    error = Signal(str)
    
    def __init__(self, filename: str, bw: generators.BinaryWaterfall):
        super().__init__()
        self.filename = filename
        self.bw = bw
        self._interrupted = False
    
    def run(self) -> None:
        try:
            # 1. Validate file exists
            self.progress.emit(10, L.export.validating_file)
            if self._interrupted:
                return
            if not os.path.isfile(self.filename):
                self.error.emit(L.dialog.file_not_found.format(filename=self.filename))
                return
            
            # 2. Delete old audio
            self.progress.emit(20, L.export.cleaning_data)
            if self._interrupted:
                return
            self.bw.delete_audio()
            
            # 3. Open file
            self.progress.emit(30, L.export.opening_file_worker)
            if self._interrupted:
                return
            self.bw.file = open(self.filename, "rb")
            self.bw.filename = os.path.realpath(self.filename)
            self.bw.file.seek(0, os.SEEK_END)
            self.bw.total_bytes = self.bw.file.tell()
            self.bw.file.seek(0)
            
            # 4. Compute audio filename
            self.progress.emit(40, L.export.preparing_audio)
            _file_path, _file_main_name = os.path.split(self.filename)
            self.bw.audio_filename = os.path.join(
                self.bw.temp_dir,
                _file_main_name + os.path.extsep + "wav"
            )
            
            # 5. Load mmap
            self.progress.emit(60, L.export.loading_mmap)
            if self._interrupted:
                return
            
            from . import rust_bridge, ngen
            _RUST_AVAILABLE: bool = False
            try:
                if rust_bridge.is_available():
                    rust_bridge.load_file(self.filename)
                    self.bw._rust_loaded = True # pyright: ignore[reportPrivateUsage]
                    _RUST_AVAILABLE: bool = True # pyright: ignore[reportConstantRedefinition]
            except Exception:
                pass
            
            if not _RUST_AVAILABLE:
                try:
                    ngen.load_file(self.filename)
                    self.bw._rust_loaded = True # pyright: ignore[reportPrivateUsage]
                except Exception:
                    self.bw._rust_loaded = False # pyright: ignore[reportPrivateUsage]
            
            # 6. Done
            self.progress.emit(100, L.export.file_load_complete)
            self.finished.emit({
                "filename": self.bw.filename,
                "total_bytes": self.bw.total_bytes,
                "audio_filename": self.bw.audio_filename,
            })
            
        except Exception as e:
            self.error.emit(str(e))
    
    def interrupt(self) -> None:
        self._interrupted = True


class AudioWorker(QThread):
    """Background worker for WAV audio generation."""
    
    progress = Signal(int, str)  # (percentage, status text)
    finished = Signal(str)       # audio_filename
    error = Signal(str)
    
    def __init__(self, bw: generators.BinaryWaterfall):
        super().__init__()
        self.bw = bw
        self._interrupted = False
    
    def run(self) -> None:
        try:
            assert self.bw.audio_filename is not None
            assert self.bw.file is not None
            assert self.bw.num_channels is not None
            assert self.bw.sample_bytes is not None
            assert self.bw.sample_rate is not None
            assert self.bw.endianness is not None
            
            # 1. Delete old audio
            self.progress.emit(5, L.export.cleaning_old_audio)
            self.bw.delete_audio()
            
            # 2. Generate WAV
            self.progress.emit(10, L.export.generating_audio_worker)
            with wave.open(self.bw.audio_filename, "wb") as f:
                f.setnchannels(self.bw.num_channels)
                f.setsampwidth(self.bw.sample_bytes)
                f.setframerate(self.bw.sample_rate)
                self.bw.file.seek(0)
                
                needs_swap = (self.bw.endianness == constants.EndiannessCode.BIG 
                             and self.bw.sample_bytes > 1)
                
                total = self.bw.total_bytes or 0
                read = 0
                assert self.bw.file is not None
                for chunk in iter(lambda: self.bw.file.read(4096), b""): # pyright: ignore[reportOptionalMemberAccess]
                    if self._interrupted:
                        return
                    
                    if needs_swap and len(chunk) >= self.bw.sample_bytes:
                        swapped = bytearray()
                        for i in range(0, len(chunk) - self.bw.sample_bytes + 1, self.bw.sample_bytes):
                            sample = chunk[i:i + self.bw.sample_bytes]
                            swapped.extend(reversed(sample))
                        remaining = len(chunk) % self.bw.sample_bytes
                        if remaining > 0:
                            swapped.extend(chunk[-remaining:])
                        f.writeframesraw(bytes(swapped))
                    else:
                        f.writeframesraw(chunk)
                    
                    read += len(chunk)
                    progress = int(10 + 60 * (read / total)) if total > 0 else 10
                    self.progress.emit(progress, L.export.generating_audio_progress.format(read=read // 1024 // 1024, total=total // 1024 // 1024))
            
            # 3. Volume adjustment
            if self.bw.volume != 100:
                self.progress.emit(75, L.export.adjusting_volume)
                if self._interrupted:
                    return
                import pydub # pyright: ignore[reportMissingTypeStubs]
                assert self.bw.volume is not None
                factor: float = self.bw.volume / 100
                audio = pydub.AudioSegment.from_file(file=self.bw.audio_filename, format="wav") # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
                audio += pydub.audio_segment.ratio_to_db(factor) # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
                temp_filename = self.bw.audio_filename + ".temp"
                audio.export(temp_filename, format="wav") # pyright: ignore[reportUnknownMemberType]
                self.bw.delete_audio()
                shutil.move(temp_filename, self.bw.audio_filename)
            
            # 4. Calculate duration
            self.progress.emit(90, L.export.calculating_duration)
            if self._interrupted:
                return
            import pydub # pyright: ignore[reportMissingTypeStubs]
            audio_length = pydub.AudioSegment.from_file(self.bw.audio_filename).duration_seconds # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
            self.bw.audio_length_ms = math.ceil(audio_length * 1000) # pyright: ignore[reportUnknownArgumentType, reportUnknownMemberType]
            
            # 5. Done
            self.progress.emit(100, L.export.audio_generation_complete)
            self.finished.emit(self.bw.audio_filename)
            
        except Exception as e:
            self.error.emit(str(e))
    
    def interrupt(self) -> None:
        self._interrupted = True


class FrameWorker(QThread):
    """Background worker for pre-rendering frames to cache."""
    
    progress = Signal(int, str)       # (percentage, status text)
    frame_ready = Signal(int, QImage) # (frame_index, frame_image)
    finished = Signal()
    error = Signal(str)
    
    def __init__(self, bw: generators.BinaryWaterfall, cache_size: int = 100):
        super().__init__()
        self.bw = bw
        self.cache_size = cache_size
        self._interrupted = False
        self._mutex = QMutex()
        self._cache: dict[int, QImage] = {}
    
    def run(self) -> None:
        try:
            if self.bw.audio_length_ms is None:
                self.error.emit(L.dialog.audio_duration_unknown)
                return
            
            # Pre-render first N frames
            fps = 30  # Default frame rate
            total_frames = min(self.cache_size, 
                              int(self.bw.audio_length_ms / 1000 * fps))
            
            for i in range(total_frames):
                if self._interrupted:
                    return
                
                ms = int(i / fps * 1000)
                try:
                    qimg = self.bw.get_frame_qimage(ms)
                    self._mutex.lock()
                    self._cache[i] = qimg
                    self._mutex.unlock()
                    self.frame_ready.emit(i, qimg)
                    
                    progress = int(10 + 80 * (i / total_frames)) if total_frames > 0 else 10
                    self.progress.emit(progress, L.export.pre_rendering_progress.format(i=i, total=total_frames))
                except Exception:
                    continue  # Skip frames that fail to render
            
            self.progress.emit(100, L.export.frame_cache_complete)
            self.finished.emit()
            
        except Exception as e:
            self.error.emit(str(e))
    
    def get_frame(self, frame_index: int) -> QImage | None:
        self._mutex.lock()
        frame = self._cache.get(frame_index)
        self._mutex.unlock()
        return frame
    
    def interrupt(self) -> None:
        self._interrupted = True
