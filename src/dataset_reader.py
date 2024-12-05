# Standard library imports.

# Related third party imports.
import xarray

# Local application/library specific imports.
from file_manager import FileManager
from settings import Settings


settings = Settings().settings
file_manager = FileManager(settings)

for file in file_manager.input_data:
    dataset = xarray.open_dataset(filename_or_obj=file)
    print(dataset.attrs)
