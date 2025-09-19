import os
import yaml


def parse_install_yaml_with_desc(file_path):
    tasks_with_desc = []
    current_task = None
    description = None

    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            # Wenn ein Task-Name gefunden wird
            if line.startswith("- name:"):
                if current_task:
                    tasks_with_desc.append({"name": current_task, "description": description})
                current_task = line.split(":", 1)[1].strip().strip('"')
                description = None  # Zurücksetzen der Beschreibung für den neuen Task
            # Beschreibung aus dem Kommentar extrahieren
            elif line.startswith("# @desc:"):
                description = line.split(":", 1)[1].strip()

        # Den letzten Task hinzufügen, wenn er existiert
        if current_task:
            tasks_with_desc.append({"name": current_task, "description": description})

    return tasks_with_desc


def generate_readme(role_name, tasks):
    readme_content = f"# {role_name}\n\n## Install Tasks\n\n"
    readme_content += "| Task Name | Description |\n"
    readme_content += "| --------- | ----------- |\n"

    for task in tasks:
        task_name = task.get('name', 'Unnamed Task')
        description = task.get('description', 'No description available.')
        readme_content += f"| {task_name} | {description} |\n"

    return readme_content


def write_readme(role_dir, content):
    readme_path = os.path.join(role_dir, 'README.md')
    with open(readme_path, 'w') as file:
        file.write(content)


def main():
    roles_dir = './roles'

    for role in os.listdir(roles_dir):
        role_dir = os.path.join(roles_dir, role)
        install_yaml = os.path.join(role_dir, 'install.yaml')

        if os.path.exists(install_yaml):
            tasks = parse_install_yaml_with_desc(install_yaml)
            readme_content = generate_readme(role, tasks)
            write_readme(role_dir, readme_content)
            print(f"README.md generated for {role}")


if __name__ == "__main__":
    main()
