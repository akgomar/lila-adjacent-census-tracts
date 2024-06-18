import pandas as pd
import geopandas as gpd

# Set directory path
dir_path = "/Users/GiaChow/Downloads"

# Load county data
lila_data = pd.read_excel(f"{dir_path}/2019 Food Access Research Atlas.xlsx")

# Load census tracts spatial data from shapefile
census_tracts = gpd.read_file("C:/Users/GiaChow/Downloads/tl_2021_40_tract/tl_2021_40_tract.shp")
print("Census Tracts Data:")
print(census_tracts.head())

# Count the number of rows in each file
num_rows_shapefile = len(census_tracts)
num_rows_excel = len(lila_data)
print(f"Number of rows in shapefile: {num_rows_shapefile}")
print(f"Number of rows in Excel file: {num_rows_excel}")

# Convert TRACT_ID columns to string
census_tracts = census_tracts.rename(columns={'GEOID': 'TRACT_ID'})
census_tracts['TRACT_ID'] = census_tracts['TRACT_ID'].astype(str)

lila_data = lila_data.rename(columns={'CensusTract': 'TRACT_ID'})
lila_data['TRACT_ID'] = lila_data['TRACT_ID'].astype(str)

# Check if specific TRACT_ID exists in either dataset
# tract_id_to_check = "40143007407"
# exists_in_excel = tract_id_to_check in lila_data['TRACT_ID'].values
# exists_in_shapefile = tract_id_to_check in census_tracts['TRACT_ID'].values

# print(f"Does TRACT_ID {tract_id_to_check} exist in Excel data? {'Yes' if exists_in_excel else 'No'}")
# print(f"Does TRACT_ID {tract_id_to_check} exist in shapefile data? {'Yes' if exists_in_shapefile else 'No'}")

# Perform a full outer merge of the LILA data with the spatial data
merged_data = pd.merge(census_tracts, lila_data, on='TRACT_ID', how='outer')
print("Merged Data Head:")
print(merged_data.head())

# Mark tracts adjacent to any LILA tract
# Create a GeoDataFrame for LILA tracts
lila_tracts = merged_data[
    (merged_data['LILATracts_1And10'] == 1) |
    (merged_data['LILATracts_halfAnd10'] == 1) |
    (merged_data['LILATracts_1And20'] == 1) |
    (merged_data['LILATracts_Vehicle'] == 1)
]

# Ensure geometry column exists for spatial operations
if 'geometry' in lila_tracts.columns:
    # Re-project to a projected CRS (e.g., UTM)
    projected_crs = "EPSG:32614"  # Example UTM zone for Oklahoma
    lila_tracts = lila_tracts.to_crs(projected_crs)

    # Buffer around LILA tracts
    buffered_lila_tracts = lila_tracts.copy()
    buffered_lila_tracts['geometry'] = buffered_lila_tracts.geometry.buffer(100)  # Buffer size in meters

    # Re-project back to the original CRS
    buffered_lila_tracts = buffered_lila_tracts.to_crs(merged_data.crs)

    # Check which tracts are adjacent
    def check_adjacency(row, buffered_gdf):
        if pd.isnull(row.geometry):
            return None
        return buffered_gdf.intersects(row.geometry).any()

    merged_data['adjacent_to_lila'] = merged_data.apply(
        lambda row: check_adjacency(row, buffered_lila_tracts), axis=1
    )
else:
    merged_data['adjacent_to_lila'] = None

print("Adjacent to LILA Data Head:")
print(merged_data[['TRACT_ID', 'adjacent_to_lila']].head())

# Create a DataFrame with the required columns
result_df = merged_data[['TRACT_ID', 'adjacent_to_lila', 'County', 'Urban', 'LowIncomeTracts', 'PovertyRate', 'MedianFamilyIncome',
                         'LILATracts_1And10', 'LILATracts_halfAnd10', 'LILATracts_1And20', 'LILATracts_Vehicle']].reset_index(drop=True)
result_df['tract_number'] = result_df.index

# Reorder the columns
result_df = result_df[['tract_number', 'TRACT_ID', 'County', 'Urban', 'LowIncomeTracts', 'PovertyRate', 'MedianFamilyIncome', 
                       'LILATracts_1And10', 'LILATracts_halfAnd10', 'LILATracts_1And20', 'LILATracts_Vehicle', 'adjacent_to_lila']]

# Print the result DataFrame to verify
print("Result DataFrame:")
print(result_df.head())

# Save the results to a CSV file
result_df.to_csv("C:/Users/GiaChow/Downloads/adjacent_tracts.csv", index=False)
print("CSV file saved successfully.")
