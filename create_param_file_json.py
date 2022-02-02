#! /usr/bin/env python
import sys
import json
import yaml
from typing import Any, Dict, Tuple, List, Union
from pathlib import Path
from collections import namedtuple

AWS_CLOUDFORMATION_PARAMETERS_SECTION_NAME = "Parameters"
AWS_CLOUDFORMATION_SECTIONS_LIST: List[str] = ["AWSTemplateFormatVersion",
                                               "Description",
                                               "Metadata",
                                               "Parameters",
                                               "Rules",
                                               "Mappings",
                                               "Conditions",
                                               "Transform",
                                               "Resources",
                                               "Outputs"]
TYPES_MAPPING = {"String": str, "Number": float, "CommaDelimitedList": lambda x: x.split(",")}

class Param(namedtuple("Param", ["name", "param_type", "description"], defaults=[""])):
    @property
    def value(self) -> str:
        return TYPES_MAPPING[self.param_type](self._value)
    
    @value.setter
    def value(self, value: str) -> None:
        self._value = value

class IsNotYamlFile(Exception):
    pass

def validate_yaml_file(yaml_path_file: Path) -> Tuple[Path, Path]:
    if not yaml_path_file.suffix.endswith(("yaml", "yml")):
        raise IsNotYamlFile(f"the file {yaml_path_file!r}"
                            " must be a yaml file or yml")
    else:
        directory_iac = yaml_path_file.parent
        return directory_iac, yaml_path_file

def main(yaml_file_path: Path, params_json_path: Path, *users: Tuple[str]) -> None:
    params = set_params_list(yaml_file_path, *users)
    print("\nSummary of parameters and its values:")
    params_dict = [{"ParameterKey": param.name,
                    "ParameterValue": param.value}
                   for param in params]
    for param in params:
        print(f"{' '*2}-Name: {param.name}")
        print(f"{' '*2}-Value: {param.value}")
    print(f"\nSaving params file json to {params_json_path}")
    with open(params_json_path, "w") as params_json_file:
        json.dump(params_dict, params_json_file, indent=4)
    print("\nFinish process!")

def set_params_list(yaml_file_path: Path, *users: Tuple[str]) -> List[Param]:
    params_metadata = extract_params_metadata(yaml_file_path)
    params = [Param(key, param_type=metadata["Type"], description=metadata.get("Description", "")) 
              for key, metadata in params_metadata.items()]
    print("Set Values for Json Params File:")
    for param in params:
        print(f"{' '*2}-Set value for param {param.name}:")
        print(f"{' '*4}-Type: {param.param_type}")
        if param.description:
            print(f"{' '*4}-Description: {param.description}")
        param.value = input(f"{' '*4}-Value: ")
        if users:
            param.value += "-" + "-".join(users)
    return params

def extract_params_metadata(yaml_file_path: Path) -> Dict[str, Any]:
    yaml_content_lines = load_file(yaml_file_path)
    yaml_param_section_content = "".join(get_params_section(yaml_content_lines))
    yaml_param_section_content_parsed = parse_yaml_params_section_content(yaml_param_section_content)
    return yaml_param_section_content_parsed

def parse_yaml_params_section_content(yaml_param_section_content: str) -> Dict[Any, Any]:
    return yaml.load(yaml_param_section_content, Loader=yaml.FullLoader)

def get_params_section(yaml_content_lines: List[str]) -> List[str]:
    yaml_content_filtered = []
    sw_found_start = False
    for index, line in enumerate(yaml_content_lines):
        if AWS_CLOUDFORMATION_PARAMETERS_SECTION_NAME in line:
            sw_found_start = True
            for param_line in yaml_content_lines[index + 1:]:
                if is_not_aws_cloudformation_sections(param_line):
                    yaml_content_filtered.append(param_line)
                else:
                    break
        if sw_found_start:
            break
    return yaml_content_filtered

def is_not_aws_cloudformation_sections(line: str) -> bool:
    for section in AWS_CLOUDFORMATION_SECTIONS_LIST:
        if section in line and section == line.rstrip().rstrip(":"):
            return False
    return True

def load_file(yaml_file_path: Path) -> List[str]:
    try:
        with open(yaml_file_path, "r") as yaml_file:
            return yaml_file.readlines()
    except FileNotFoundError:
        raise FileNotFoundError(f"{yaml_file_path!r} yaml file does not exists")

if __name__ == "__main__":
    directory_iac, yaml_file_path = validate_yaml_file(Path(sys.argv[1])) # this must be a yaml file
    params_file_path = directory_iac / "params.json"
    users = sys.argv[2:]
    try:
        main(yaml_file_path, params_file_path, *users)
    except (KeyboardInterrupt) as error:
        print(f"\nProccess Terminated! {error}")