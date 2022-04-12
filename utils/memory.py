import ctypes
import struct
from win32con import PROCESS_ALL_ACCESS, PROCESS_VM_READ
from constants import BYTES_TO_READ

kernel32 = ctypes.WinDLL("kernel32.dll")


def write_process_memory(pid, memory_address, data, bytes_to_write):
    """A function that gets a pid of a process, a memory address, data and a number of bytes,
     and writes the data to the specified address."""
    data_in_bytes = data.to_bytes(bytes_to_write, byteorder="little")
    handle = kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
    buffer = ctypes.create_string_buffer(data_in_bytes)
    kernel32.WriteProcessMemory(handle, memory_address, buffer, bytes_to_write, None)
    kernel32.CloseHandle(handle)


def read_process_memory(pid, memory_address, number_of_bytes_to_read):
    """A function that gets a pid of a process, a memory address and a number of bytes,
     and returns the value of the specified bytes."""
    handle = kernel32.OpenProcess(PROCESS_VM_READ, False, pid)
    buffer = (ctypes.c_byte * number_of_bytes_to_read)()
    bytes_read = ctypes.c_ulonglong()
    kernel32.ReadProcessMemory(handle, memory_address, buffer, number_of_bytes_to_read, ctypes.byref(bytes_read))
    kernel32.CloseHandle(handle)
    return struct.unpack(BYTES_TO_READ[number_of_bytes_to_read], buffer)[0]
