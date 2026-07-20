from collections.abc import Callable

from .general import grouper # pyright: ignore[reportUnknownVariableType]


def get_luminance(r: int, g: int, b: int) -> float:
    return ((0.299 * r) + (0.587 * g) + (0.114 * b)) / 0xFF


def pick_shade_from_luminance(r: int, g: int, b: int, light_shade: int=0xFF, dark_shade: int=0x00) -> tuple[int, int, int]:
    if get_luminance(r, g, b) < 0.5:
        return light_shade, light_shade, light_shade
    else:
        return dark_shade, dark_shade, dark_shade


def desaturate(r: int, g: int, b: int) -> tuple[int, int, int]:
    gray_value = round((min(r, g, b) + max(r, g, b)) / 2)

    return gray_value, gray_value, gray_value


def invert(r: int, g: int, b: int) -> tuple[int, int, int]:
    return (0xFF - r, 0xFF - g, 0xFF - b)


def average(r1: int, g1: int, b1: int, r2: int, g2: int, b2: int) -> tuple[int, int, int]:
    return (round((r1 + r2) / 2), round((g1 + g2) / 2), round((b1 + b2) / 2))


def split_rgb_byte(bytestring: tuple[int, ...]) -> tuple[int, int, int]:
    r = bytestring[0]
    g = bytestring[1]
    b = bytestring[2]

    return r, g, b


def filter_rgb_bytes(bytestring: bytes, filter_function: Callable[[int, int, int], tuple[int, int, int]]) -> bytes:
    result = bytes()
    for byte in grouper(bytestring, 3, 0x00):
        r, g, b = split_rgb_byte(byte)
        r_filtered, g_filtered, b_filtered = filter_function(r, g, b)
        result += bytes([r_filtered, g_filtered, b_filtered])

    return result


def average_rgb_bytes(bytestring_a: bytes, bytestring_b: bytes):
    result = bytes()
    for byte_a, byte_b in zip(grouper(bytestring_a, 3, 0x00), grouper(bytestring_b, 3, 0x00)):
        r_a, g_a, b_a = split_rgb_byte(byte_a)
        r_b, g_b, b_b = split_rgb_byte(byte_b)
        r_average, g_average, b_average = average(r_a, g_a, b_a, r_b, g_b, b_b)
        result += bytes([r_average, g_average, b_average])

    return result
