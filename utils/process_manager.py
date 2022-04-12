import os
from constants import PIDS_FILE_PATH, PID, STATUS, AVAILABLE
from utils.winmine_exe import WinmineExe


def get_all_pids():
    """A functions that returns all the pids of running winmines."""
    command = "tasklist | findstr Winmine__XP.exe"
    pids = []
    process_description_lines = os.popen(command).read().split("\n")
    for line in process_description_lines:
        try:
            pids.append(int(line.split()[1]))
        except IndexError:
            pass
    return remove_new_lines(pids)


def get_available_pids():
    """A function that returns all available pids."""
    available_pids = []
    with open(PIDS_FILE_PATH) as file:
        pids_and_status = file.readlines()
        for pid_and_status in pids_and_status:
            try:
                pid, status = pid_and_status.split()[PID], pid_and_status.split()[STATUS]
                if status == AVAILABLE:
                    available_pids.append(int(pid))
            except IndexError:
                pass
    return remove_new_lines(available_pids)


def change_pid_status(pid):
    """A function that gets a pid and changes its status."""
    new_text = ""
    with open(PIDS_FILE_PATH) as file:
        pids_and_status = file.readlines()
        for pid_and_status in pids_and_status:
            try:
                p, status = pid_and_status.split()[PID], pid_and_status.split()[STATUS]
                if p == str(pid):
                    new_text += str(p) + " " + str(1 - int(status)) + "\n"
                else:
                    new_text += pid_and_status
            except IndexError:
                pass
    with open(PIDS_FILE_PATH, "w") as file:
        file.write(new_text)


def get_all_pids_in_file():
    """A function that returns all the pids in the pids file."""
    pid_list = []
    with open(PIDS_FILE_PATH) as file:
        pids_and_status = file.readlines()
        for pid_and_status in pids_and_status:
            pid_list.append(pid_and_status.split()[PID])
    return remove_new_lines(pid_list)


def add_pid_to_file(pid):
    """A function that gets a pid and adds it to the pids file."""
    with open(PIDS_FILE_PATH, "a") as file:
        file.write((str(pid) + " " + AVAILABLE + "\n"))


def remove_pid_from_file(pid):
    """A function that gets a pid and removes it from the pids file."""
    new_text = ""
    with open(PIDS_FILE_PATH) as file:
        pids_and_status = file.readlines()
        for pid_and_status in pids_and_status:
            try:
                p, status = pid_and_status.split()[PID], pid_and_status.split()[STATUS]
                if p != str(pid):
                    new_text += pid_and_status
            except IndexError:
                pass
    with open(PIDS_FILE_PATH, "w") as file:
        file.write(new_text)


def does_exist(pid):
    """A function that gets a pid and returns true if it exists, and false if it doesn't"""
    with open(PIDS_FILE_PATH) as file:
        pids_and_status = file.readlines()
        for pid_and_status in pids_and_status:
            if str(pid_and_status.split()[PID]) == str(pid):
                return True
    return False


def remove_duplicates_from_file():
    pids_dict = {}
    pids_in_file = get_all_pids_in_file()
    for pid in pids_in_file:
        if pid in pids_dict.keys():
            pids_dict[pid] += 1
        else:
            pids_dict[pid] = 1
    for pid in pids_dict.keys():
        if pids_dict[pid] > 1:
            remove_pid_from_file(pid)
            break


def update_pids_file():
    """A function that updates the pids file (removes pids of processes that are not running anymore,
        and adds the pid of new running processes)."""
    running_processes = get_all_pids()

    for pid in running_processes:
        if not does_exist(pid):
            add_pid_to_file(pid)
    pids_in_file = get_all_pids_in_file()
    for pid in pids_in_file:
        if int(pid) not in running_processes:
            remove_pid_from_file(pid)
    remove_duplicates_from_file()


def get_winmines(pid_lst) -> list[WinmineExe]:
    """A function that returns a list of winmines objects connected to the specified pids."""
    lst_winmines = []
    for pid in pid_lst:
        lst_winmines.append(WinmineExe(pid))
    return lst_winmines


def remove_new_lines(list_line):
    new_list = []
    for line in list_line:
        if line != "\n":
            new_list.append(line)
    return new_list
