import os
import glob
from pathlib import Path


def get_most_recent_comic():
    """
    Find the most recent xkcd comic in the data directory.
    Returns: tuple of (date, comic_title, image_path) or None if no comic found
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(project_root, 'data')

    if not os.path.exists(data_dir):
        print(f"Data directory not found: {data_dir}")
        return None

    # Get all date directories, sorted in reverse order (most recent first)
    date_dirs = sorted([d for d in os.listdir(data_dir)
                       if os.path.isdir(os.path.join(data_dir, d))],
                      reverse=True)

    if not date_dirs:
        print("No date directories found in data folder")
        return None

    # Get the most recent date directory
    most_recent_date = date_dirs[0]
    most_recent_dir = os.path.join(data_dir, most_recent_date)

    # Find PNG files in that directory
    png_files = glob.glob(os.path.join(most_recent_dir, '*.png'))

    if not png_files:
        print(f"No PNG files found in {most_recent_dir}")
        return None

    # Get the first PNG file (there should typically be only one)
    image_path = png_files[0]
    comic_title = Path(image_path).stem  # Get filename without extension

    # Return relative path from project root
    rel_image_path = os.path.relpath(image_path, project_root)

    # URL-encode spaces for GitHub compatibility
    rel_image_path = rel_image_path.replace(' ', '%20')

    return (most_recent_date, comic_title, rel_image_path)


def update_readme():
    """
    Update the README.md file with the most recent xkcd comic.
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    readme_path = os.path.join(project_root, 'README.md')

    comic_info = get_most_recent_comic()

    if not comic_info:
        print("No comic found to update README")
        return

    date, title, image_path = comic_info

    # Create the README content
    readme_content = f"""# Safely Endangered Comics Daily

#### {date}

## {title}

![{title}]({image_path})

---

*This README is automatically updated with the latest xkcd comic.*
"""

    # Write to README
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)

    print(f"README updated successfully with comic: {title}")


if __name__ == "__main__":
    update_readme()

