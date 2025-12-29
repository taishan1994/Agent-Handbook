import os

THRESHOLD_MB = 20
THRESHOLD_BYTES = THRESHOLD_MB * 1024 * 1024
GITIGNORE = ".gitignore"


def is_leaf_dir(path: str) -> bool:
    """是否是最后一层目录（不包含子目录）"""
    for entry in os.scandir(path):
        if entry.is_dir():
            return False
    return True


def get_dir_size(path: str) -> int:
    total = 0
    for root, _, files in os.walk(path):
        for f in files:
            fp = os.path.join(root, f)
            if os.path.isfile(fp):
                try:
                    total += os.path.getsize(fp)
                except OSError:
                    pass
    return total


def load_gitignore() -> set:
    if not os.path.exists(GITIGNORE):
        return set()
    with open(GITIGNORE, "r") as f:
        return set(line.strip() for line in f if line.strip())


def append_to_gitignore(paths):
    if not paths:
        return
    with open(GITIGNORE, "a") as f:
        f.write("\n# Auto ignored large leaf directories (>20MB)\n")
        for p in paths:
            f.write(f"{p}\n")


def main(root="."):
    ignored = load_gitignore()
    to_add = []

    for cur_root, dirs, _ in os.walk(root):
        # 跳过 .git 等
        dirs[:] = [d for d in dirs if not d.startswith(".")]

        if not is_leaf_dir(cur_root):
            continue

        size = get_dir_size(cur_root)
        if size >= THRESHOLD_BYTES:
            rel_path = os.path.relpath(cur_root, root)
            if not rel_path.endswith("/"):
                rel_path += "/"

            if rel_path not in ignored:
                print(f"[IGNORE] {rel_path} ({size / 1024 / 1024:.2f} MB)")
                to_add.append(rel_path)

    append_to_gitignore(to_add)


if __name__ == "__main__":
    main()
