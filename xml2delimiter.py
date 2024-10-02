import json
import logging
import os
import re
import sys
import time
from collections import OrderedDict
from typing import Tuple, Dict, Any, List, Union
from lxml import etree

class XMLProcessor:
    def __init__(self):
        # Set default separator and whitespace stripping flag
        self.BAR = "|"
        self.STRIP_WHITESPACE = True
        
        # Initialize start time and buffer for processing nodes in batches
        self.start_time = time.time()
        self.buffer = []  # Buffer to collect node data
        self.buffer_size = 1000  # Size of the buffer for batch processing

    def parse_cli_args(self) -> Tuple[str, str, str, OrderedDict]:
        # Check for sufficient command-line arguments
        if len(sys.argv) < 4:
            logging.error("Insufficient arguments provided.")
            sys.exit("Usage: script.py <source_xml> <config_json> <output_file> [options]")

        source_xml, config_json, output_file = sys.argv[1:4]

        # Check if the input files exist
        if not all(map(os.path.isfile, [source_xml, config_json])):
            logging.error("Input files not found.")
            raise FileNotFoundError("Input files not found.")

        # Check if the output directory exists
        if not os.path.exists(os.path.dirname(output_file)):
            logging.error("Output directory does not exist.")
            raise FileNotFoundError("Output directory does not exist.")

        # Load configuration from JSON file
        try:
            with open(config_json, 'r') as f:
                config = json.load(f, object_pairs_hook=OrderedDict)
        except json.JSONDecodeError:
            logging.exception(f"Invalid JSON configuration: {config_json}")
            raise

        # Parse additional command-line options
        options = dict(arg.split('=') for arg in sys.argv[4:] if '=' in arg)
        self.BAR = options.get('bar', self.BAR)
        self.STRIP_WHITESPACE = options.get('strip', 'true').lower() not in ['false', 'no', 'n', '0']

        return source_xml, config_json, output_file, config

    def safe_xpath(self, node: etree.Element, path: str) -> List[etree.Element]:
        # Safely evaluate an XPath expression, handle errors if any
        try:
            return node.xpath(path)
        except (etree.XPathEvalError, etree.XPathError) as e:
            logging.error(f"XPath error for path '{path}' in node '{node.tag}': {e}")
            raise

    def parse_field_path(self, path: str) -> Tuple[str, Union[str, None]]:
        # Parse an XPath and an optional attribute
        node_path, attribute = re.match(r'^(.*?)(=\w+)?$', path).groups()
        return node_path or '.', attribute.lstrip('=') if attribute else None

    def clean_value(self, value: Any) -> str:
        # Clean and format the value; strip whitespace if the flag is set
        if value is None:
            return ''
        value = str(value)
        return value.strip() if self.STRIP_WHITESPACE else value

    def format_line(self, code: str, node: etree.Element, fields: List[str]) -> str:
        # Extract values based on the provided fields and format them as a line
        values = []
        for field in fields:
            if not field:
                values.append('')
                continue

            # Parse field path and attribute
            xpath, attr = self.parse_field_path(field)
            matches = self.safe_xpath(node, xpath)

            # Get attribute or text value from the matched elements
            if not matches:
                values.append('')
            elif attr:
                values.append(matches[0].attrib.get(attr, ''))
            else:
                values.append(matches[0].text)

        # Clean values and join them with the separator
        values = list(map(self.clean_value, values))
        line = self.BAR.join([code] + values) + "\n"
        return line if any(values) else ""

    def process_node(self, node: Union[etree.Element, List[etree.Element]], template: Dict) -> str:
        # Recursively process nodes based on the given template
        output = ""
        if isinstance(node, list):
            # If a list of nodes, process each one
            for item in node:
                output += self.process_node(item, template)
        else:
            # Process the node according to the template
            for code, value in template.items():
                if isinstance(value, list):
                    output += self.format_line(code, node, value)
                elif isinstance(value, dict):
                    sub_nodes = self.safe_xpath(node, code)
                    output += self.process_node(sub_nodes, value)
        return output

    def node_processor(self, args: Tuple[str, Dict]) -> str:
        # Process a single node (XML string) and template
        node_str, template = args
        # Clean the node XML string to remove namespaces and attributes
        node_str = re.sub(r"xmlns.*=\".*?\"", "", node_str)
        node_str = re.sub(r'\s\w+?:(\w+?=".*?)', r" \g<1>", node_str)
        node = etree.fromstring(node_str)
        return self.process_node(node, template)

    def node_generator(self, xml_file: str, root_templates: Dict) -> Any:
        # Yield nodes from the XML file that match the root tags in the template
        root_tags = [f"{{*}}{tag}" for tag in root_templates.keys()]

        for _, node in etree.iterparse(xml_file, tag=root_tags, huge_tree=True):
            template = root_templates[etree.QName(node).localname]
            yield etree.tostring(node, encoding='unicode'), template
            node.clear()  # Clear node to free memory

    def get_root_templates(self, template: Dict) -> OrderedDict:
        # Get root templates from the configuration
        root_templates = OrderedDict()
        for key, value in template.items():
            if isinstance(value, list):
                root_templates.setdefault(None, OrderedDict())[key] = value
            else:
                root_templates[key] = value
        return root_templates

    def write_buffer_to_file(self, out):
        #Writes the contents of the buffer to the output file and clears the buffer.
        if self.buffer:
            out.write(''.join(self.buffer).encode('utf-8'))
            self.buffer.clear()  # Clear buffer after writing

    def show_conversion_progress(self, count: int):
        # Display conversion progress in the console
        elapsed = time.time() - self.start_time
        rate = round(count / elapsed) if elapsed > 0 else 0
        sys.stderr.write(f"Processed: {count} ({rate} nodes/sec)\r")
        
    def print_summary(self, processed_count: int):
        #Prints the total nodes processed and the time taken.
        end_time = time.time()
        total_time = end_time - self.start_time
        print(f"\nTotal nodes processed: {processed_count}")
        print(f"Time required: {total_time:.2f} seconds")
        print("\nProcessing completed.")

    def run(self):
        # Initialize logging configuration
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

        # Parse command-line arguments
        source_xml, config_json, output_file, config = self.parse_cli_args()

        processed_count = 0  # Initialize the count of processed nodes

        with open(output_file, 'wb') as out:
            root_templates = self.get_root_templates(config)

            # Process nodes based on templates
            for nodeData in self.node_generator(source_xml, root_templates):
                self.buffer.append(self.node_processor(nodeData))  # Add node data to buffer
                processed_count += 1  # Increment the count of processed nodes

                # Write buffer to file when it reaches the specified size
                if len(self.buffer) >= self.buffer_size:
                    self.write_buffer_to_file(out)

                # Update the progress display every 100 nodes
                if processed_count % 100 == 0:
                    self.show_conversion_progress(processed_count)

            # Write any remaining data in the buffer to the output file
            self.write_buffer_to_file(out)

        # Show final progress after processing is complete
        self.show_conversion_progress(processed_count)

        # Print total nodes processed and time taken
        self.print_summary(processed_count)

if __name__ == '__main__':
    processor = XMLProcessor()
    processor.run()
