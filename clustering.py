import pandas as pd
import numpy as np
from scipy.cluster.hierarchy import linkage, to_tree
from scipy.spatial.distance import cdist



df = pd.read_csv("west_bengal_warehouses.csv")
df.loc[74, 'capacity'] = 0


df['Latitude'] = pd.to_numeric(df['Latitude'], errors='coerce')
df['Longitude'] = pd.to_numeric(df['Longitude'], errors='coerce')


coords = df[['Latitude', 'Longitude']].values.astype('float64')


# This is the "map" of how clusters are connected
Z = linkage(coords, method='ward')


# --- 3. The "Climb the Tree" Function ---
def get_k_nearest_hierarchical_up(target_id, k, dataframe, linkage_matrix):
    try:
        target_idx = dataframe.index[dataframe['Warehouse_ID'] == target_id][0]
    except IndexError:
        return "Warehouse ID not found."
    
    rootnode, nodelist = to_tree(linkage_matrix, rd=True)
    current_node = nodelist[target_idx]
    
    
    while True:
        # Get indices of all warehouses in the current cluster branch
        branch_indices = current_node.pre_order()
        
        # Count how many have capacity > 0 (excluding the target itself)
        valid_neighbors = dataframe.iloc[branch_indices]
        valid_count = len(valid_neighbors[
            (valid_neighbors['Warehouse_ID'] != target_id) & 
            (valid_neighbors['capacity'] > 0)
        ])
        
        
        if valid_count >= k or current_node.id >= (2 * len(dataframe) - 2):
            break
            
        # Otherwise, find the parent in the linkage matrix and keep climbing
        found_parent = False
        for i, merge in enumerate(linkage_matrix):
            if merge[0] == current_node.id or merge[1] == current_node.id:
                parent_id = i + len(dataframe)
                current_node = nodelist[parent_id]
                found_parent = True
                break
        if not found_parent:
            break
    
    # --- PREPARE FINAL DATA ---
    final_branch_df = dataframe.iloc[current_node.pre_order()].copy()
    
    # Calculate Distances
    target_coords = dataframe.loc[[target_idx], ['Latitude', 'Longitude']].values.astype('float64')
    branch_coords = final_branch_df[['Latitude', 'Longitude']].values.astype('float64')
    final_branch_df['Distance'] = cdist(target_coords, branch_coords, metric='euclidean')[0]
    
    
    result = final_branch_df[
        (final_branch_df['Warehouse_ID'] != target_id) & 
        (final_branch_df['capacity'] > 0)
    ].sort_values('Distance').head(k)
    
    return result





# target_wh = "WH_090"
# nearest_smart = get_k_nearest_hierarchical_up(target_wh, 10, df, Z)

# print(f"--- Hierarchical Neighbors for {target_wh} ---") 
# print(nearest_smart[['Warehouse_ID', 'Nearest_Hub', 'Distance', 'capacity','Latitude','Longitude',]])
# print(nearest_smart[nearest_smart['capacity']==min(nearest_smart['capacity'])])