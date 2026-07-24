from __future__ import annotations
from typing import Any, cast
from moviepy import VideoClip # pyright: ignore[reportMissingTypeStubs]

import os
import shutil
import math
import time
import tempfile
import pydub # pyright: ignore[reportMissingTypeStubs]
from moviepy import ImageSequenceClip, AudioFileClip # pyright: ignore[reportMissingTypeStubs]
from PIL import Image
from PySide6.QtCore import QUrl, Qt
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QProgressDialog, QMessageBox

from . import generators, helpers, constants
from .lang import L
from .workers import FileWorker, AudioWorker, FrameWorker


# Image playback class
#   Provides an abstraction for displaying images and audio in the GUI
class Player:
    def __init__(self,
                 binary_waterfall: generators.BinaryWaterfall,
                 display: Any,
                 set_playbutton_function: Any | None = None,
                 set_seekbar_function: Any | None = None,
                 max_dim: int = cast(int, constants.DEFAULTS["max_dim"]),
                 fps: float = cast(float, constants.DEFAULTS["player_fps"])
                 ) -> None:
        self.image: QImage | None = None
        self.volume: int = 0
        self.fps: float = 0.0
        self.frame_ms: int = 0
        self.height: int = 0
        self.width: int = 0
        self.dim: tuple[int, int] = (0, 0)
        self.max_dim: int = 0

        self.bw = binary_waterfall

        self.display = display

        self.set_dims(max_dim=max_dim)

        self.set_play_button = set_playbutton_function
        self.set_seekbar_function = set_seekbar_function

        # Initialize player as black
        self.clear_image()

        # Make the QMediaPlayer for audio playback
        self.audio = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.audio.setAudioOutput(self.audio_output)

        # Set audio playback settings
        self.set_volume(100)

        # Set set_image_timestamp to run when the audio position is changed
        self.audio.positionChanged.connect(self.set_image_timestamp) # pyright: ignore[reportUnknownMemberType]
        self.audio.positionChanged.connect(self.set_seekbar_if_given) # pyright: ignore[reportUnknownMemberType]
        # Also, make sure it's updating more frequently (default is too slow when playing)
        self.fps_min = 1
        self.fps_max = 120
        self.set_fps(fps)

        # Setup change state handler
        self.audio.playbackStateChanged.connect(self.state_changed_handler) # pyright: ignore[reportUnknownMemberType]
        
        # Async workers
        self.file_worker: FileWorker | None = None
        self.audio_worker: AudioWorker | None = None
        self.frame_worker: FrameWorker | None = None
        self.progress_dialog: QProgressDialog | None = None

    def __del__(self) -> None:
        self.running = False

    def set_dims(self, max_dim: int) -> None:
        self.max_dim = max_dim
        assert self.bw.width is not None
        assert self.bw.height is not None
        if self.bw.width > self.bw.height:
            self.width = round(max_dim)
            self.height = round(self.width * (self.bw.height / self.bw.width))
        else:
            self.height = round(max_dim)
            self.width = round(self.height * (self.bw.width / self.bw.height))

        self.dim = (self.width, self.height)

    def set_fps(self, fps: float) -> None:
        self.fps = min(max(fps, self.fps_min), self.fps_max)
        self.frame_ms = math.floor(1000 / self.fps)

    def clear_image(self) -> None:
        background_image = Image.new(
            mode="RGBA",
            size=(self.width, self.height),
            color=constants.COLORS["viewer"]
        )

        background_image = generators.Watermarker().mark(background_image)

        img_bytestring = background_image.convert("RGB").tobytes()

        qimg = QImage(
            img_bytestring,
            self.width,
            self.height,
            3 * self.width,
            QImage.Format.Format_RGB888
        )

        self.set_image(qimg)

    def update_dims(self, max_dim: int) -> None:
        # Change dims
        self.set_dims(max_dim=max_dim)

        # Update image
        if self.bw.filename is None:
            self.clear_image()
        else:
            assert self.image is not None
            self.set_image(self.image)

    def refresh_dims(self) -> None:
        self.update_dims(self.max_dim)

    def set_volume(self, volume: int) -> None:
        self.volume = volume
        self.audio_output.setVolume(volume / 100.0)

    def scale_image(self, image: QImage) -> QImage:
        return image.scaled(self.width, self.height)

    def set_image(self, image: QImage) -> None:
        self.image = self.scale_image(image)

        # Compute the QPixmap version
        qpixmap = QPixmap.fromImage(self.image)

        # Set the picture
        self.display.setPixmap(qpixmap)

    def get_position(self) -> int:
        return self.audio.position()

    def get_duration(self) -> int:
        return self.audio.duration()

    def set_position(self, ms: int) -> None:
        duration = self.get_duration()

        # Validate it's in range, and if it's not, clip it
        ms = math.ceil(ms)
        if ms < 0:
            ms = 0
        if ms > duration:
            ms = duration

        if self.bw.filename is not None:
            self.audio.setPosition(ms)

        # If the file is at the end, pause
        if ms == duration:
            self.pause()

    def set_playbutton_if_given(self, play: bool) -> None:
        if self.set_play_button is not None:
            self.set_play_button(play=play)

    def set_seekbar_if_given(self, ms: int) -> None:
        if self.set_seekbar_function is not None:
            self.set_seekbar_function(ms)

    def state_changed_handler(self, media_state: QMediaPlayer.PlaybackState) -> None:
        if media_state == QMediaPlayer.PlaybackState.PlayingState:
            self.set_playbutton_if_given(play=False)
        elif media_state == QMediaPlayer.PlaybackState.PausedState:
            self.set_playbutton_if_given(play=True)
        elif media_state == QMediaPlayer.PlaybackState.StoppedState:
            self.set_playbutton_if_given(play=True)

    def play(self) -> None:
        self.audio.play()

    def pause(self) -> None:
        self.audio.pause()

    def forward(self, ms: int = 5000) -> None:
        new_pos = self.get_position() + ms
        self.set_position(new_pos)

    def back(self, ms: int = 5000) -> None:
        new_pos = self.get_position() - ms
        self.set_position(new_pos)

    def frame_forward(self) -> None:
        self.forward(ms=self.frame_ms)

    def frame_back(self) -> None:
        self.back(ms=self.frame_ms)

    def restart(self) -> None:
        self.set_position(0)

    def set_audio_file(self, filename: str | None) -> None:
        if filename is None:
            url = QUrl("")
        else:
            url = QUrl.fromLocalFile(self.bw.audio_filename)
        self.audio.setSource(url)

    def open_file(self, filename: str | None) -> None:
        self.close_file()

        if filename is None:
            return
        
        # Show progress bar
        self._show_progress_bar(L.progress.opening_file)
        
        # Start FileWorker
        self.file_worker = FileWorker(filename, self.bw)
        self.file_worker.progress.connect(self._on_worker_progress) # pyright: ignore[reportUnknownMemberType]
        self.file_worker.finished.connect(self._on_file_ready) # pyright: ignore[reportUnknownMemberType]
        self.file_worker.error.connect(self._on_worker_error) # pyright: ignore[reportUnknownMemberType]
        self.file_worker.start()
    
    def _on_file_ready(self, info: dict) -> None: # pyright: ignore[reportUnknownParameterType, reportMissingTypeArgument]
        self.update_progress(40, L.progress.generating_audio)
        
        # Start AudioWorker
        self.audio_worker = AudioWorker(self.bw)
        self.audio_worker.progress.connect(self._on_worker_progress) # pyright: ignore[reportUnknownMemberType]
        self.audio_worker.finished.connect(self._on_audio_ready) # pyright: ignore[reportUnknownMemberType]
        self.audio_worker.error.connect(self._on_worker_error) # pyright: ignore[reportUnknownMemberType]
        self.audio_worker.start()
    
    def _on_audio_ready(self, audio_path: str) -> None:
        self.set_audio_file(audio_path)
        self.set_playbutton_if_given(play=True)
        self.update_progress(90, L.progress.pre_rendering_frames)
        
        # Start FrameWorker after audio is ready (needs audio_length_ms)
        self.frame_worker = FrameWorker(self.bw)
        self.frame_worker.progress.connect(self._on_worker_progress) # pyright: ignore[reportUnknownMemberType]
        self.frame_worker.frame_ready.connect(self._on_frame_ready) # pyright: ignore[reportUnknownMemberType]
        self.frame_worker.finished.connect(self._on_frames_ready) # pyright: ignore[reportUnknownMemberType]
        self.frame_worker.error.connect(self._on_worker_error) # pyright: ignore[reportUnknownMemberType]
        self.frame_worker.start()
        
        self.set_image_timestamp(0)
    
    def _on_frame_ready(self, index: int, frame: QImage) -> None:
        # Frame cached, available for playback
        pass
    
    def _on_frames_ready(self) -> None:
        # All frames pre-rendered
        self._hide_progress_bar()
    
    def _on_worker_progress(self, percent: int, text: str) -> None:
        self.update_progress(percent, text)
    
    def _on_worker_error(self, error: str) -> None:
        self._hide_progress_bar()
        QMessageBox.critical(None, L.dialog.error, error)
    
    def _show_progress_bar(self, text: str) -> None:
        self.progress_dialog = QProgressDialog(text, None, 0, 100)
        self.progress_dialog.setWindowTitle(L.progress.opening_file)
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.setValue(0)
        self.progress_dialog.show()
    
    def update_progress(self, percent: int, text: str) -> None:
        dialog = self.progress_dialog
        if dialog is None:
            return
        try:
            dialog.setValue(percent)
            dialog.setLabelText(text)
        except (RuntimeError, AttributeError):
            self.progress_dialog = None
    
    def _hide_progress_bar(self) -> None:
        dialog = self.progress_dialog
        if dialog is None:
            return
        self.progress_dialog = None
        try:
            dialog.close()
        except (RuntimeError, AttributeError):
            pass

    def close_file(self) -> None:
        # Interrupt all running workers
        for worker in [self.file_worker, self.audio_worker, self.frame_worker]:
            if worker and worker.isRunning():
                worker.interrupt()
                worker.wait(3000)  # Wait up to 3 seconds
        
        self.file_worker = None
        self.audio_worker = None
        self.frame_worker = None
        
        # Hide progress bar
        self._hide_progress_bar()
        
        self.pause()

        # Disconnect signals temporarily to avoid state_changed_handler during cleanup
        try:
            self.audio.playbackStateChanged.disconnect(self.state_changed_handler) # pyright: ignore[reportUnknownMemberType]
        except TypeError:
            pass

        self.audio.stop()
        time.sleep(0.001)  # Without a short delay here, we crash
        self.set_audio_file(None)

        self.bw.change_filename(None)

        self.restart()
        self.clear_image()

        # Reconnect signals
        self.audio.playbackStateChanged.connect(self.state_changed_handler) # pyright: ignore[reportUnknownMemberType]
        self.set_playbutton_if_given(play=True)

    def file_is_open(self) -> bool:
        if self.bw.filename is None:
            return False
        else:
            return True

    def is_playing(self) -> bool:
        if self.audio.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            return True
        else:
            return False

    def set_image_timestamp(self, ms: int) -> None:
        if self.bw.filename is None:
            self.clear_image()
        else:
            self.set_image(self.bw.get_frame_qimage(ms))

    def update_image(self) -> None:
        ms = self.get_position()
        self.set_image_timestamp(ms)

    def set_audio_settings(self,
                           num_channels: int,
                           sample_bytes: int,
                           sample_rate: int,
                           volume: int,
                           endianness: constants.EndiannessCode = constants.EndiannessCode.LITTLE
                           ) -> None:
        # Stop playback and release file lock before regenerating audio
        self.audio.stop()
        self.set_audio_file(None)

        self.bw.set_audio_settings(
            num_channels=num_channels,
            sample_bytes=sample_bytes,
            sample_rate=sample_rate,
            volume=volume,
            endianness=endianness
        )
        # Re-open newly computed file
        self.set_audio_file(self.bw.audio_filename)


# Renderer class
#   Provides an abstraction for rendering images, audio, and video to files
class Renderer:
    def __init__(self,
                 binary_waterfall: generators.BinaryWaterfall,
                 ) -> None:
        self.bw = binary_waterfall

    def export_frame(self,
                     ms: int,
                     filename: str,
                     size: tuple[int, int] | None = None,
                     keep_aspect: bool = False
                     ) -> None:
        helpers.make_file_path(filename)

        if self.bw.audio_filename is None:
            # If no file is loaded, make a black image
            source = Image.new(
                mode="RGBA",
                size=(self.bw.width or 1, self.bw.height or 1),
                color="#000"
            )
        else:
            source = self.bw.get_frame_image(ms).convert("RGBA")

        # Resize with aspect ratio, paste onto black
        if size is None:
            resized = source
        else:
            if keep_aspect:
                output_size: tuple[int, int] = helpers.get_size_for_fit_frame(content_size=source.size, frame_size=size)["size"] # pyright: ignore[reportAssignmentType]
            else:
                output_size: tuple[int, int] = size

            resized = helpers.fit_to_frame(
                image=source,
                frame_size=output_size,
                scaling=Image.Resampling.NEAREST,
                transparent=False
            )

        final = resized.convert("RGB")

        final.save(filename)

    def export_audio(self, filename: str) -> None:
        _filename_main, filename_ext = os.path.splitext(filename)
        filename_ext = filename_ext.lower()

        helpers.make_file_path(filename)

        if filename_ext == constants.AudioFormatCode.WAVE.value:
            # Just copy the .wav file
            assert self.bw.audio_filename is not None
            shutil.copy(self.bw.audio_filename, filename)
        elif filename_ext in [
            constants.AudioFormatCode.MP3.value,
            constants.AudioFormatCode.FLAC.value,
            constants.AudioFormatCode.OGG.value,
            constants.AudioFormatCode.M4A.value
        ]:
            # Use Pydub for format conversion (requires ffmpeg)
            assert self.bw.audio_filename is not None
            try:
                audio = pydub.AudioSegment.from_wav(self.bw.audio_filename) # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
                if filename_ext == constants.AudioFormatCode.MP3.value:
                    audio.export(filename, format="mp3") # pyright: ignore[reportUnknownMemberType]
                elif filename_ext == constants.AudioFormatCode.FLAC.value:
                    audio.export(filename, format="flac") # pyright: ignore[reportUnknownMemberType]
                elif filename_ext == constants.AudioFormatCode.OGG.value:
                    audio.export(filename, format="ogg", codec="libvorbis") # pyright: ignore[reportUnknownMemberType]
                elif filename_ext == constants.AudioFormatCode.M4A.value:
                    audio.export(filename, format="ipod", codec="aac") # pyright: ignore[reportUnknownMemberType]
            except Exception as e:
                error_msg = str(e)
                if "ffmpeg" in error_msg.lower() or "winerror 2" in error_msg.lower():
                    raise RuntimeError(L.dialog.ffmpeg_not_found) from e
                raise RuntimeError(L.dialog.audio_export_error.format(error=str(e))) from e

    def get_frame_count(self, fps: float) -> int:
        audio_duration = self.bw.get_audio_length() / 1000
        frame_count = round(audio_duration * fps)

        return frame_count

    def export_sequence(self,
                        directory: str,
                        fps: float,
                        size: tuple[int, int] | None = None,
                        keep_aspect: bool = False,
                        image_format: constants.ImageFormatCode | None = None,
                        progress_dialog: QProgressDialog | None = None
                        ) -> None:
        helpers.make_file_path(directory)

        frame_count = self.get_frame_count(fps)

        frame_number_digits = len(str(frame_count))

        if image_format is None:
            image_format = constants.ImageFormatCode.PNG

        for frame in range(frame_count + 1):
            frame_number = str(frame).rjust(frame_number_digits, "0")
            frame_filename = os.path.join(directory, f"{frame_number}{image_format.value}")
            frame_ms = round((frame / fps) * 1000)

            if progress_dialog is not None:
                progress_dialog.setValue(frame)

                if progress_dialog.wasCanceled():
                    return

            self.export_frame(
                ms=frame_ms,
                filename=frame_filename,
                size=size,
                keep_aspect=keep_aspect
            )

        if progress_dialog is not None:
            progress_dialog.setValue(frame_count)

    def export_video(self,
                     filename: str,
                     fps: float,
                     size: tuple[int, int] | None = None,
                     keep_aspect: bool = False,
                     progress_dialog: QProgressDialog | None = None,
                     codec: str | None = None,
                     audio_codec: str | None = None,
                     bitrate: str | None = None,
                     audio_bitrate: str | None = None,
                     preset: str | None = None
                     ) -> None:
        # Get temporary directory
        temp_dir = tempfile.mkdtemp()

        # Make file names
        image_dir = os.path.join(temp_dir, "images")
        audio_file = os.path.join(temp_dir, "audio.wav")
        _filename_main, filename_ext = os.path.splitext(filename)
        filename_path, _filename_title = os.path.split(filename)
        video_file = os.path.join(temp_dir, f"video{filename_ext}")

        # Set progress dialog to not close when at max
        if progress_dialog is not None:
            progress_dialog.setAutoReset(False)

        # Export image sequence
        self.export_sequence(
            directory=image_dir,
            fps=fps,
            size=size,
            keep_aspect=keep_aspect,
            image_format=constants.ImageFormatCode.PNG,
            progress_dialog=progress_dialog
        )

        if progress_dialog is not None:
            if progress_dialog.wasCanceled():
                shutil.rmtree(temp_dir)
                return
            progress_dialog.setLabelText(L.progress.splicing_final_video)

        # Export audio
        self.export_audio(audio_file)

        # Prepare the custom logger to update the progress box
        if progress_dialog is not None:
            custom_logger = helpers.QtBarLoggerMoviepy(progress_dialog=progress_dialog)
        else:
            custom_logger = "bar"

        # Make a list of the image filenames
        frames_list: list[str] = list()
        for frame_filename in os.listdir(image_dir):
            full_frame_filename = os.path.join(image_dir, frame_filename)
            frames_list.append(full_frame_filename)

        # Merge image sequence and audio into final video
        sequence_clip = ImageSequenceClip(frames_list, fps=fps)
        audio_clip = AudioFileClip(audio_file)

        video_clip: VideoClip = sequence_clip.with_audio(audio_clip)
        video_clip.write_videofile(
            filename=video_file,
            codec=codec,
            bitrate=bitrate,
            audio_codec=audio_codec,
            audio_bitrate=audio_bitrate,
            preset=preset,
            threads=None,
            logger=custom_logger,
            temp_audiofile=None,
            temp_audiofile_path=temp_dir
        )

        if progress_dialog is not None:
            if progress_dialog.wasCanceled():
                shutil.rmtree(temp_dir)
                return

            # Reset progress dialog and set to exit on completion
            progress_dialog.setLabelText(L.progress.wrapping_up)
            progress_dialog.setValue(0)
            progress_dialog.setMaximum(100)
            progress_dialog.setAutoReset(True)

        # Move video to final location
        os.makedirs(filename_path, exist_ok=True)
        shutil.move(video_file, filename)

        # Delete temporary files
        shutil.rmtree(temp_dir)

        if progress_dialog is not None:
            progress_dialog.setValue(100)
