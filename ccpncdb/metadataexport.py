import datetime
import json

class MetadataExport:
    """Metadata export class"""

    def metadata_clearance(self, json_result):
        """
        Cleans up metadata by removing redundant fields and restructuring specific entries.

        Parameters:
        json_result (dict): The input JSON dictionary containing metadata.
        is_archive (bool, optional): Flag indicating if the metadata is part of an archive. Defaults to False.

        Returns:
        json_result (dict): A cleaned-up dictionary with redundant fields removed and specific entries restructured.
        """
        # Remove redundant fields from the dictionary if they exist
        keys_to_remove = ['isChecked', '_id', 'user_name', 'id', 'chemname_tokens', 'visible', 'last_modified', 'Z','last_version']

        # Remove the keys from the dictionary if they exist
        for key in keys_to_remove:
            if key in json_result:
                del json_result[key]

        json_result['ORCID'] = json_result['orcid']['path']
        del json_result['orcid']

        return json_result
                                                                                                                                                                                                                                                                                                                                           
    def metadata_cleanup(self, json_result, version_num, file_id = None):
        """
        Cleans up and reorders metadata for a given JSON dataset.

        This function processes a JSON dictionary containing metadata, performing the following operations:
        - Finds and stores the matching metadata in 'version_metadata' for the user specified record version 
          using magresfilesID as reference.
        - Cleans up the date and calculation metadata.
        - Reorders the keys in the resulting dictionary according to a predefined order.

        Parameters:
        json_result (dict): The input JSON dictionary containing metadata.
        file_id (str, optional): The file ID to match within the 'version_history'. Defaults to None.
        is_archive (bool, optional): Flag indicating if the metadata is part of an archive. Defaults to False.

        Returns:
        json_result_ordered (dict): A new dictionary with cleaned and reordered metadata.
        """
        json_result_new = {}
        for key in json_result:
            if key == 'version_history':
                
                json_result_new['version'] = f"{int(version_num)+1}"
                json_result_new['latest_version'] = json_result['version_count']

                json_buffer = json_result[key][int(version_num)]
                del json_buffer['magresFilesID']
                for item in json_buffer:
                    if item == 'date':
                        json_buffer[item] = self.format_date(json_buffer[item])
                    elif item == 'magres_calc':
                        json_buffer[item] = self.calc_metadata_extract(json_buffer[item])
                    else:
                        json_buffer[item] = json_buffer[item]

                json_result_new['version_metadata'] = json_buffer
            else:
                json_result_new[key] = json_result[key]
        del json_result_new['version_count']

        json_result_ordered = self.reorder_keys(json_result_new)

        return json_result_ordered
    
    def reorder_keys(self, json_result):
        """
        Reorders the keys in a given JSON dictionary according to a predefined order.The resulting dictionary will 
        contain only the keys that are present in the predefined list and in the input dictionary, arranged in the 
        specified order. Keys that are not in the predefined list will be omitted from the resulting dictionary.

        Parameters:
        json_result (dict): The input JSON dictionary whose keys need to be reordered.

        Returns:
        json_result_reordered (dict): A new dictionary with keys ordered according to the predefined list.

        Note:
        - The predefined order of keys is specified in the 'ordered_keys' list.
        - Only keys present in both the 'ordered_keys' list and the input dictionary will be included in the output.
        - The function does not modify the input dictionary; it returns a new dictionary with the reordered keys.
        """
        # Define the desired order of keys in the dictionary
        ordered_keys = ['chemname', 'ORCID', 'type', 'immutable_id', 'version', 'latest_version', 'version_metadata', 'formula', 'stochiometry', 'elements', 'elements_ratios', 'chemical_formula_descriptive', 'nelements','molecules','nmrdata']

        # Reorder the keys in the dictionary
        json_result_ordered = {key: json_result[key] for key in ordered_keys if key in json_result}

        return json_result_ordered
    
    def format_date(self, date_str):
        """
        Formats a date string into a standardised form. If the date string matches any of the predefined formats, 
        it is converted to the standardised format "%Y-%m-%d %H:%M:%S". If none of the formats match, a ValueError
        is raised.

        Parameters:
        date_str (str): The input date string to be formatted.

        Returns:
        date str: The formatted date string in the standardised format "%Y-%m-%d %H:%M:%S".

        Raises:
        ValueError: If the input date string does not match any of the predefined formats.

        Note:
        - The function supports the following date formats:
        - "%Y-%m-%d %H:%M:%S.%f" (e.g., "2021-12-25 16:23:34.123456")
        - "%Y-%m-%d %H:%M:%S" (e.g., "2021-12-25 16:23:34")
        - "%a, %d %b %Y %H:%M:%S %Z" (e.g., "Thu, 19 Sep 2024 10:10:36 GMT")
        """
        date_formats= [
            "%Y-%m-%d %H:%M:%S.%f",  # Existing format with microseconds
            "%Y-%m-%d %H:%M:%S",     # Existing format without microseconds
            "%a, %d %b %Y %H:%M:%S %Z"  # New format (e.g., "Thu, 19 Sep 2024 10:10:36 GMT") for CI tests
            ]
        for date_format in date_formats:
            try:
                dt = datetime.datetime.strptime(date_str, date_format)
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue

        # If none of the formats match, raise an error
        raise ValueError(f"Date format not recognized: {date_str}")
    
    def calc_metadata_extract(self, calc_string):
        """
        Extracts calculation metadata from a JSON string and formats into a dictionary.

        If the input string is None, it returns a dictionary with an error message indicating that calculation 
        metadata is unavailable (only possible in CI tests). Otherwise, it parses the JSON string and formats 
        the metadata.

        Parameters:
        calc_string (str): The input JSON string containing calculation metadata. Can be None.

        Returns:
        target_dict (dict): A dictionary containing the extracted and formatted calculation metadata.
        """
        target_dict = {}
        if calc_string is None:
            # This metadata error is in place for CI tests that may not have calculation metadata,
            # Magres files in the database should by default contain calculation metadata, so this 
            # code block should not be reached
            target_dict = {"Metadata Error": "Calculation metadata unavailable"}
        else:
            calc_string_unwrap = json.loads(calc_string)
            for dict_elem in calc_string_unwrap:
                if len(calc_string_unwrap[dict_elem][0]) == 1:
                    target_dict[dict_elem] = calc_string_unwrap[dict_elem][0][0]
                elif dict_elem == 'calc_pspot':
                    final_elem = []
                    for elem in calc_string_unwrap[dict_elem]:
                        final_elem.append(' '.join(elem))
                        target_dict[dict_elem] = final_elem
                else:
                    target_dict[dict_elem] = ' '.join(calc_string_unwrap[dict_elem][0])

        return target_dict