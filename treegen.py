import json
import os
import sys
import hashlib
import pyperclip
from pathlib import Path

HASH_RESULT_LENGTH = 8
BYTE_BUFFER_SIZE = 128 * 1024
MAXIMUM_FILE_SIZE = 1 * 1024 * 1024  # 1MB
assert 0 < HASH_RESULT_LENGTH <= 64
assert 0 < BYTE_BUFFER_SIZE <= 1024 * 1024


class TreeGenerator:
    space = '    '
    branch = '│   '
    tee = '├── '
    last = '└── '

    def __init__(self, exclude_extensions=None, exclude_folders=None):
        self.exclude_extensions = exclude_extensions
        self.exclude_folders = exclude_folders

    @staticmethod
    def sha256sum(filename):
        if not Path(filename).exists():
            return HASH_RESULT_LENGTH * 'f'
        h = hashlib.sha256()
        b = bytearray(BYTE_BUFFER_SIZE)
        mv = memoryview(b)
        if Path(filename).stat().st_size > MAXIMUM_FILE_SIZE:
            return HASH_RESULT_LENGTH * 'f'
        with open(filename, 'rb', buffering=0) as f:
            for n in iter(lambda: f.readinto(mv), 0):
                h.update(mv[:n])
        return h.hexdigest()[0:HASH_RESULT_LENGTH]

    def generate(self, path, prefix_path=''):
        contents = list(path.iterdir())
        pointers = [self.tee] * (len(contents) - 1) + [self.last]
        project_path_length = len(str(Path.cwd()))
        for pointer, path in zip(pointers, contents):
            name = str(path)[project_path_length + 1:]
            if self.exclude_folders is not None and any(
                    name.startswith(folder) for folder in self.exclude_folders):
                continue
            if self.exclude_extensions is not None and any(
                    name.endswith(extension) for extension in self.exclude_extensions):
                continue
            # print(name, file=sys.stderr)
            prefix = self.sha256sum(str(path)) + ' ' if path.is_file() else ''
            yield prefix_path + pointer + prefix + path.name
            if path.is_dir():
                extension = self.branch if pointer == self.tee else self.space
                yield from self.generate(path, prefix_path=prefix_path + extension)

    def print_tree(self, path):
        path = Path(path)
        assert path.exists() and path.is_dir()
        content = 'Directory structure of ' + str(path) + '\n\n'
        for line in self.generate(path):
            content += line + '\n'
        print(content, file=sys.stdout)
        content += '\nList of hidden folders\n\n'
        for folder in self.exclude_folders:
            content += folder + '\n'
        content += '\nList of hidden extensions\n\n'
        for extension in self.exclude_extensions:
            content += extension + '\n'
        pyperclip.copy(content)  # copy to clipboard


def get_settings():
    print("Choose settings file in exclude folder")
    exclude_folder_path = str(Path(__file__).parent) + "/exclude"
    settings_files = os.listdir(exclude_folder_path)
    print("0. Use default settings file (treegen.settings.json)")
    for i in range(len(settings_files)):
        print(str(i + 1) + ". " + str(Path(exclude_folder_path + "/" + settings_files[i]).resolve()))
    settings_file_index = int(input("Enter index of settings file: "))
    if settings_file_index == 0:
        settings_file_path = str(Path(__file__).parent) + "/treegen.settings.json"
    else:
        settings_file_path = exclude_folder_path + "/" + settings_files[settings_file_index - 1]
    print("Using settings file: " + settings_file_path)
    with open(settings_file_path, 'r') as json_file:
        data = json.load(json_file)
    # return data["exclude_folders_arg"], data["exclude_extensions_arg"]
    try:
        exclude_folders = data["exclude_folders_arg"]
        exclude_extensions = data["exclude_extensions_arg"]
        return exclude_folders, exclude_extensions
    except KeyError:
        print("Invalid settings file")
        return None, None


def main():
    print("Current file directory: " + str(Path(__file__).parent))
    print("Current working directory: " + str(Path.cwd()))
    exclude_folders_arg, exclude_extensions_arg = get_settings()
    tree_gen = TreeGenerator(exclude_folders=exclude_folders_arg, exclude_extensions=exclude_extensions_arg)
    directory = input('Enter directory (default = current directory): ')
    if directory == '':
        directory = str(Path.cwd())
    tree_gen.print_tree(directory)


if __name__ == '__main__':
    main()
