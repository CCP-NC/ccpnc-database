import datetime
import json

class MetadataExport:
    """Metadata export class"""

    def metadata_clearance(self, json_result, is_archive=False):
        # Remove redundant fields from the dictionary if they exist

        # Define direct keys to remove from the dictionary
        keys_to_remove = ['isChecked', '_id', 'user_name', 'id', 'chemname_tokens', 'visible', 'version_count', 'last_modified', 'Z']
        # Remove the keys from the dictionary if they exist
        for key in keys_to_remove:
            if key in json_result:
                del json_result[key]

        if json_result['last_version']['extref_other'] is None:
            del json_result['last_version']['extref_other']

        # If metadata is added to archive, remove version_history and retain last_version. Otherwise, do vice-versa.
        if is_archive:
            del json_result['version_history']
            del json_result['last_version']['magresFilesID']
        else:
            del json_result['last_version']

        return json_result
    
    def metadata_cleanup(self, json_result, file_id = None, is_archive=False):

        # If metadata is added to archive, edit date and magres_calc fields in last_version. 
        # For single JSON file download, rename version_history to download_version, edit and include relevant version's metadata.
        if is_archive:
            json_result['last_version']['date'] = self.format_date(json_result['last_version']['date'])
            json_result['last_version']['magres_calc'] = self.calc_metadata_extract(json_result['last_version']['magres_calc'])
            json_result_new = json_result
        else:
            json_result_new = {}
            for key in json_result:
                if key == 'version_history':
                    json_buffer_temp = json_result[key]
                    json_buffer = {}
                    for index in range(len(json_buffer_temp)):
                        if json_buffer_temp[index]['magresFilesID'] == file_id:
                            del json_buffer_temp[index]['magresFilesID']
                            for item in json_buffer_temp[index]:
                                if item == 'date':
                                    json_buffer[item] = self.format_date(json_buffer_temp[index][item])
                                elif item == 'magres_calc':
                                    json_buffer[item] = self.calc_metadata_extract(json_buffer_temp[index][item])
                                else:
                                    json_buffer[item] = json_buffer_temp[index][item]
                    new_key = 'download_version'
                    json_result_new[new_key] = json_buffer
                else:
                    json_result_new[key] = json_result[key]

        return json_result_new
    
    def format_date(self, date_str):
        try:
            dt = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S.%f")
        except ValueError:
            dt = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    
    def calc_metadata_extract(self, calc_string):
        calc_string_unwrap = json.loads(calc_string)
        target_dict = {}
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