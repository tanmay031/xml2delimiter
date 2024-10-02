
# XML to Delimited File Processor

## Overview

This project is a Python-based utility for converting XML files into various delimited formats (e.g., bar-delimited) using a customizable JSON template. It is designed for data processing needs where services require input in a specific delimited format.

## Project Structure

```
project-directory/
│
├── xml2delimiter.py         # Main script for processing XML files
├── template.json            # JSON template defining XML structure mapping
├── sample_input.xml         # Sample XML file for testing
├── README.md                # Project documentation
└── output.txt               # Output file in delimited format
```

**Key Features**

- **XML Parsing:** Utilizes `lxml` for efficient XML processing with XPath for precise data extraction.
- **Customizable Output:** The output format is defined by a JSON template, allowing flexibility for different delimiters.
- **Buffered Writing:** Uses a buffer to write output, optimizing performance.
- **Logging:** Implements logging for error handling and process tracking.


## Usage

Run the script with the following command:

```bash
python xml2delimiter.py <source_xml> <config_json> <output_file> [options]
```

### Example Command

```bash
python xml2delimiter.py sample_input.xml template.json output.txt bar='|' strip='true'
```

## Sample Input

Here's an example of the `sample_input.xml` file:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<library_catalog>
  <header>
    <file_version>1.0</file_version>
    <creation_date>2023-09-26</creation_date>
  </header>

  <library>
    <book>
      <title>The Great Gatsby</title>
      <author name="F. Scott Fitzgerald"/>
      <publication_year>1925</publication_year>
      <isbn>9780743273565</isbn>
      <genre>Classic Literature</genre>
      <summary>A story of decadence and excess in Jazz Age America</summary>
      <price value="12.99" currency="USD"/>
      <in_stock>true</in_stock>
    </book>
    <!-- Additional book entries -->
  </library>

  <footer>
    <total_books>1</total_books>
    <last_updated>2023-09-26T14:30:00Z</last_updated>
  </footer>
</library_catalog>
```

## Example JSON Template

Here’s a brief example of the JSON template used to define the structure:

```json
{
  "header": {
    "000": [
      "file_version",
      "creation_date"
    ]
  },
  "book": {
    "100": [
      "title",
      "author=name",
      "publication_year",
      "isbn"
    ],
    "200": [
      "genre",
      "summary"
    ],
    "300": [
      "price=value",
      "price=currency",
      "in_stock"
    ]
  },
  "footer": {
    "999": [
      "total_books",
      "last_updated"
    ]
  }
}
```

## Record Layout

The record layout defines how the output delimited file will be structured. Each section corresponds to different parts of the XML structure, as outlined below:

```
000|header/file_version|header/creation_date
100|book/title|book/author=name|book/publication_year|book/isbn
200|book/genre|book/summary
300|book/price=value|book/price=currency|book/in_stock
999|footer/total_books|footer/last_updated
```

## Sample Output

Given the above input, the generated `output.txt` file might look like this:

```
000|1.0|2023-09-26
100|The Great Gatsby|F. Scott Fitzgerald|1925|9780743273565
200|Classic Literature|A story of decadence and excess in Jazz Age America
300|12.99|USD|true
999|1|2023-09-26T14:30:00Z
```

