import yaml

LARGE_MODEL = "ollama:llama3.1:8b"
SMALL_MODEL = "ollama:granite3.3:2b"


def read_yaml_file(file_path):
    """
    Reads a YAML file from the given file path and returns its content as a Python dictionary.

    :param file_path: The path to the YAML file on the disk.
    :return: A Python dictionary interpreting the content of the YAML file.
    """
    try:
        with open(file_path, 'r') as file:
            # Use yaml.safe_load() to parse the YAML file into a Python dictionary
            parsed_dict = yaml.safe_load(file)
        return parsed_dict
    except FileNotFoundError:
        raise FileNotFoundError(f"The file at path '{file_path}' was not found.")
    except Exception as e:
        raise ValueError(f"Error reading YAML file: {e}")
