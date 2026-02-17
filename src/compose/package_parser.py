from PyQt6.QtCore import Qt
import xml.etree.ElementTree as ET
import json
import locale


def parse_packages_xml(xml_string: str) -> list:
    if xml_string is None:
        print("Warning: XML string is None, returning empty list")
        return []

    try:
        tree = ET.ElementTree(ET.fromstring(xml_string))
    except ET.ParseError as e:
        print(f"Failed to parse XML: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error parsing XML: {e}")
        return []

    root = tree.getroot()

    sections = []
    locale_lang, _ = locale.getdefaultlocale()
    if locale_lang is None:
        locale_lang = "en_US"

    for section_elem in root.findall('section'):
        section_id = section_elem.get('id')
        section_name = section_elem.get('name')
        section_nouserselect = section_elem.get('nouserselect', '') == 'true'

        if section_name and section_name.startswith('{') and section_name.endswith('}'):
            try:
                section_name_dict = json.loads(section_name)
                section_name = section_name_dict.get(locale_lang, section_name)
            except json.JSONDecodeError:
                pass

        packages = []
        for package_elem in section_elem.findall('package'):
            versions = []
            for version_elem in package_elem.findall('version'):
                try:
                    version_info = {
                        'name': version_elem.get('name'),
                        'code': version_elem.get('code'),
                        'downloadurl': version_elem.get('downloadurl'),
                        'filetype': version_elem.get('filetype'),
                        'installto': version_elem.get('installto'),
                        'unpack': version_elem.get('unpack')
                    }
                    versions.append(version_info)
                except Exception:
                    continue

            if versions:
                package_version = versions[0].get('name', '')
            else:
                package_version = package_elem.get('version', '')

            package_info = {
                'id': package_elem.get('id'),
                'name': package_elem.get('name'),
                'version': package_version,
                'description': package_elem.get('description', ''),
                'official': package_elem.get('official', '') == 'true',
                'type': package_elem.get('type', ''),
                'author': package_elem.get('author', ''),
                'required': package_elem.get('required', '') == 'true',
                'default': package_elem.get('default', '') == 'true',
                'nouserselect': package_elem.get('nouserselect', '') == 'true'
            }

            package_info['versions'] = versions

            if package_info.get('name') and package_info['name'].startswith('{') and package_info['name'].endswith('}'):
                try:
                    package_name_dict = json.loads(package_info['name'])
                    package_info['name'] = package_name_dict.get(locale_lang, package_info['name'])
                except json.JSONDecodeError:
                    pass

            packages.append(package_info)

        sections.append({
            'id': section_id,
            'name': section_name,
            'nouserselect': section_nouserselect,
            'packages': packages
        })

    return sections


def populate_install_selector(install_selector, sections: list):
    if not install_selector:
        print("Warning: install_selector is None")
        return

    for section in sections:
        try:
            section_hide_checkbox = section.get('nouserselect', False)

            group_item = install_selector.add_component_group(
                section.get('name', 'Unknown Section'),
                f"Section ID: {section.get('id', 'N/A')}",
                hide_checkbox=section_hide_checkbox
            )

            for package in section.get('packages', []):
                if package.get('nouserselect'):
                    is_checked = package.get('default', True)
                else:
                    is_checked = package.get('default', False) or package.get('required', False)

                hide_checkbox = package.get('required', False) or package.get('nouserselect', False)

                component_item = install_selector.add_component(
                    group_item,
                    package.get('name', 'Unknown Package'),
                    f"{package.get('description', '')} (v{package.get('version', '')})",
                    checked=is_checked,
                    hide_checkbox=hide_checkbox,
                    component_id=package.get('id')
                )

                if 'versions' in package and package['versions']:
                    component_item.setData(0, Qt.ItemDataRole.UserRole + 2, package['versions'])
                    component_item.setData(0, Qt.ItemDataRole.UserRole + 3, package.get('version'))
        except Exception as e:
            print(f"Error populating section {section.get('id')}: {e}")
            continue
