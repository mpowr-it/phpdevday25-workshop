import os


def generate_directory_tree(start_path, indent="  "):
    tree_str = ""
    for root, dirs, files in os.walk(start_path):
        level = root.replace(start_path, '').count(os.sep)
        indent_str = indent * (level)
        tree_str += f"{indent_str}└ {os.path.basename(root)}\n"
        sub_indent = indent * (level + 1)
        for f in files:
            tree_str += f"{sub_indent}└ {f}\n"
    return tree_str


def generate_readme(role_name, directory_tree):
    readme_content = f"## Module Tree for {role_name}\n\n"
    readme_content += "```\n"
    readme_content += directory_tree
    readme_content += "```\n"
    return readme_content


def write_readme(role_dir, content):
    readme_path = os.path.join(role_dir, 'README.md')
    with open(readme_path, 'a') as file:  # Appending to the existing README.md
        file.write(content)


def main():
    roles_dir = './roles'

    for role in os.listdir(roles_dir):
        role_dir = os.path.join(roles_dir, role)

        if os.path.isdir(role_dir):
            print(f"Generating directory tree for: {role}")
            directory_tree = generate_directory_tree(role_dir)
            readme_content = generate_readme(role, directory_tree)
            write_readme(role_dir, readme_content)
            print(f"Directory tree added to README.md for {role}")


if __name__ == "__main__":
    main()
