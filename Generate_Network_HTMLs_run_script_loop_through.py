import os
import duckdb
import geopandas as gpd
import numpy as np
import pandas as pd
import lonboard as lb
from lonboard import Map, PathLayer, basemap
from lonboard.colormap import apply_categorical_cmap
from lonboard.layer_extension import PathStyleExtension
from Generate_Network_HTML_functions import *
import warnings

warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning)

working_dir = "c:/Data/Network_HTMLs/"
raw_file_dir = os.path.join(working_dir, "1_Raw_Summary_Loaded_Network_Links")
output_dir = os.path.join(working_dir, "4_HTML_outputs")

rc_scenarios = [
   "Y2018_RC25v1_02", "Y2026_RC25v1_02", "Y2031_RC25v1_02", "Y2036_RC25v1_02", "Y2041_RC25v1_02", "Y2046_RC25v1_02", "Y2051_RC25v1_02", "Y2056_RC25v1_02",\
   "Y2026_RC25v1_02_CF", "Y2031_RC25v1_02_CF", "Y2036_RC25v1_02_CF", "Y2041_RC25v1_02_CF"
]

pipeline_scenarios = ["Y2031_RC25v1_02_PLv1", "Y2031_RC25v1_02_PLv2", "Y2031_RC25v1_02_PLv3"]

scenarios1 = pipeline_scenarios
scenarios2 = pipeline_scenarios

for scenario1 in scenarios1:
    for scenario2 in scenarios2:
        if scenario1 == scenario2:
            continue
        scenario_base_name = scenario1
        scenario_compare_name = scenario2

        # Create temporary storage for duckdb, remove if already exists
        store_db = "store.db"
        if os.path.exists(store_db):
            os.remove(store_db)
            print(f"File '{store_db}' deleted successfully.")
        else:
            print(f"File '{store_db}' does not exist.")

        if 'con' in globals():
            con.close()
        con = duckdb.connect()
        con.load_extension("spatial")

        columns = "A, B, VEH_AM, VEH_IP, VEH_PM, VEH_OP, VEH_WD, VC_AM, VC_IP, VC_PM, VC_OP, HYCAP_AM, HYCAP_IP, HYCAP_PM, HYCAP_OP, CSPD_AM, CSPD_IP, CSPD_PM, CSPD_OP, LANES_AM, LANES_IP, LANES_PM, LANES_OP"
        scenario_base_dir = os.path.join(working_dir, raw_file_dir, f"SUMMARY_LOADED_NETWORK_LINKS_{scenario_base_name}.shp")
        scenario_compare_dir = os.path.join(working_dir, raw_file_dir,
                                            f"SUMMARY_LOADED_NETWORK_LINKS_{scenario_compare_name}.shp")

        print("Loading layers into the database...")
        # Create a 'links' temp table
        con.sql(f"""
                CREATE TABLE IF NOT EXISTS base_links AS 
                SELECT 
                        A, B, COLUMNS('LINKC_'), COLUMNS('SL'),
                        CAST(ST_AsWKB(ST_FlipCoordinates(ST_Transform(geom, 'EPSG:20255', 'EPSG:4326'))) AS VARCHAR) AS geometry
                FROM '{scenario_base_dir}' 
                """)
        con.sql(f"""
                CREATE TABLE IF NOT EXISTS compare_links AS 
                SELECT 
                        A, B, COLUMNS('LINKC_'), COLUMNS('SL'),
                        CAST(ST_AsWKB(ST_FlipCoordinates(ST_Transform(geom, 'EPSG:20255', 'EPSG:4326'))) AS VARCHAR) AS geometry
                FROM '{scenario_compare_dir}' 
                """)
        # Create a 'after' temp table
        con.sql(f"""
                CREATE TABLE IF NOT EXISTS after AS 
                SELECT {columns}, geom
                FROM '{scenario_compare_dir}' 
                --WHERE LINKC_AM != 25
                """)
        # Create a 'before' temp table
        con.sql(f"""
                CREATE TABLE IF NOT EXISTS before AS 
                SELECT {columns} 
                FROM '{scenario_base_dir}' 
                --WHERE LINKC_AM != 25
                """)

        diff = con.sql("""
            WITH 
                merged AS 
                (
                    SELECT 
                        a.A, a.B,
                        a.VEH_AM AS VEH_AM_after,
                        a.VEH_IP AS VEH_IP_after,
                        a.VEH_PM AS VEH_PM_after,
                        a.VEH_OP AS VEH_OP_after,
                        a.VEH_WD AS VEH_WD_after,
                        b.VEH_AM AS VEH_AM_before,
                        b.VEH_IP AS VEH_IP_before,
                        b.VEH_PM AS VEH_PM_before,
                        b.VEH_OP AS VEH_OP_before,
                        b.VEH_WD AS VEH_WD_before,
                        a.HYCAP_AM AS HYCAP_AM_after,
                        a.HYCAP_IP AS HYCAP_IP_after,
                        a.HYCAP_PM AS HYCAP_PM_after,
                        a.HYCAP_OP AS HYCAP_OP_after,
                        b.HYCAP_AM AS HYCAP_AM_before,
                        b.HYCAP_IP AS HYCAP_IP_before,
                        b.HYCAP_PM AS HYCAP_PM_before,
                        b.HYCAP_OP AS HYCAP_OP_before,
                        a.LANES_AM AS LANES_AM_after,
                        a.LANES_IP AS LANES_IP_after,
                        a.LANES_PM AS LANES_PM_after,
                        a.LANES_OP AS LANES_OP_after,
                        b.LANES_AM AS LANES_AM_before,
                        b.LANES_IP AS LANES_IP_before,
                        b.LANES_PM AS LANES_PM_before,
                        b.LANES_OP AS LANES_OP_before,
                    FROM after AS a
                    FULL OUTER JOIN before AS b
                    USING (A, B)
                ),
                diff AS 
                (
                    SELECT 
                        A, B,
                        VEH_AM_after - VEH_AM_before AS VEH_AM_DIFF,
                        VEH_IP_after - VEH_IP_before AS VEH_IP_DIFF,
                        VEH_PM_after - VEH_PM_before AS VEH_PM_DIFF,
                        VEH_OP_after - VEH_OP_before AS VEH_OP_DIFF,
                        VEH_WD_after - VEH_WD_before AS VEH_WD_DIFF,
                        (HYCAP_AM_after - HYCAP_AM_before) / 2 AS HYCAP_AM_DIFF,
                        (HYCAP_IP_after - HYCAP_IP_before) / 6 AS HYCAP_IP_DIFF,
                        (HYCAP_PM_after - HYCAP_PM_before) / 3 AS HYCAP_PM_DIFF,
                        (HYCAP_OP_after - HYCAP_OP_before) / 6 AS HYCAP_OP_DIFF,
                        LANES_AM_after - LANES_AM_before AS LANES_AM_DIFF,
                        LANES_IP_after - LANES_IP_before AS LANES_IP_DIFF,
                        LANES_PM_after - LANES_PM_before AS LANES_PM_DIFF,
                        LANES_OP_after - LANES_OP_before AS LANES_OP_DIFF,
                    FROM merged
                )
            SELECT * from diff
        """)
        print("Finished loading layers into the database.")

        base_links = con.sql("from base_links WHERE LINKC_AM NOT IN (1,-1,0) AND LINKC_AM < 39 AND LINKC_AM < 50;").to_df()
        compare_links = con.sql(
            "from compare_links WHERE LINKC_AM NOT IN (1,-1,0) AND LINKC_AM < 39 AND LINKC_AM < 50;").to_df()
        master_links = pd.concat([base_links, compare_links])
        master_links = master_links.drop_duplicates(subset=['A', 'B'], keep='last')

        diff_with_geo = diff.to_df().merge(
            master_links,
            on=['A', 'B'],
            how="inner"
        )

        base_vc = con.sql("select * from before").to_df().merge(
            master_links,
            on=['A', 'B'],
            how="inner"
        )

        compare_vc = con.sql("select * from after").to_df().merge(
            master_links,
            on=['A', 'B'],
            how="inner"
        )

        gdf_input = create_gdf_using_decoded_geoms(diff_with_geo).reset_index()
        base_vc_gdf = create_gdf_using_decoded_geoms(base_vc).reset_index()
        compare_vc_gdf = create_gdf_using_decoded_geoms(compare_vc).reset_index()

        print("Preparing maps...")
        vol_cols = ["VEH_AM_DIFF", "VEH_IP_DIFF", "VEH_PM_DIFF", "VEH_OP_DIFF", "VEH_WD_DIFF"]
        for col in vol_cols:
            generate_volume_diff_plot(gdf_input, col, 100,
                                      os.path.join(output_dir, f"{scenario_compare_name}_vs_{scenario_base_name}_{col}.html"))
            insert_jp_ui_font_family(os.path.join(output_dir, f"{scenario_compare_name}_vs_{scenario_base_name}_{col}.html"))

        cap_cols = ["HYCAP_AM_DIFF", "HYCAP_IP_DIFF", "HYCAP_PM_DIFF", "HYCAP_OP_DIFF"]
        for col in cap_cols:
            generate_network_diff_plot(gdf_input, col, 1,
                                       os.path.join(output_dir, f"{scenario_compare_name}_vs_{scenario_base_name}_{col}.html"))
            insert_jp_ui_font_family(os.path.join(output_dir, f"{scenario_compare_name}_vs_{scenario_base_name}_{col}.html"))

        lane_cols = ["LANES_AM_DIFF", "LANES_IP_DIFF", "LANES_PM_DIFF", "LANES_OP_DIFF"]
        for col in lane_cols:
            generate_nlanes_plot(gdf_input, col, 1,
                                       os.path.join(output_dir, f"{scenario_compare_name}_vs_{scenario_base_name}_{col}.html"))
            insert_jp_ui_font_family(os.path.join(output_dir, f"{scenario_compare_name}_vs_{scenario_base_name}_{col}.html"))

        # Raw volumes and capacity
        vol_raw_cols = ["VEH_AM", "VEH_IP", "VEH_PM", "VEH_OP", "VEH_WD"]
        for col in vol_raw_cols:
            generate_volume_diff_plot(base_vc_gdf, col, 100,
                                      os.path.join(output_dir, f"{scenario_base_name}_{col}.html"))
            insert_jp_ui_font_family(os.path.join(output_dir, f"{scenario_base_name}_{col}.html"))
            generate_volume_diff_plot(compare_vc_gdf, col, 100,
                                      os.path.join(output_dir, f"{scenario_compare_name}_{col}.html"))
            insert_jp_ui_font_family(os.path.join(output_dir, f"{scenario_compare_name}_{col}.html"))

        cap_raw_cols = ["HYCAP_AM", "HYCAP_IP", "HYCAP_PM", "HYCAP_OP"]
        for col in cap_raw_cols:
            generate_network_diff_plot(base_vc_gdf, col, 1,
                                       os.path.join(output_dir, f"{scenario_base_name}_{col}.html"))
            insert_jp_ui_font_family(os.path.join(output_dir, f"{scenario_base_name}_{col}.html"))
            generate_network_diff_plot(compare_vc_gdf, col, 1,
                                       os.path.join(output_dir, f"{scenario_compare_name}_{col}.html"))
            insert_jp_ui_font_family(os.path.join(output_dir, f"{scenario_compare_name}_{col}.html"))

        lane_raw_cols = ["LANES_AM", "LANES_IP", "LANES_PM", "LANES_OP"]
        for col in lane_raw_cols:
            generate_nlanes_plot(base_vc_gdf, col, 1,
                                       os.path.join(output_dir, f"{scenario_base_name}_{col}.html"))
            insert_jp_ui_font_family(os.path.join(output_dir, f"{scenario_base_name}_{col}.html"))
            generate_nlanes_plot(compare_vc_gdf, col, 1,
                                       os.path.join(output_dir, f"{scenario_compare_name}_{col}.html"))
            insert_jp_ui_font_family(os.path.join(output_dir, f"{scenario_compare_name}_{col}.html"))

        time_periods = ["AM", "IP", "PM", "OP"]
        for tp in time_periods:
            generate_vc_plot(base_vc_gdf, tp, 100, os.path.join(output_dir, f"{scenario_base_name}_VC_{tp}.html"))
            insert_jp_ui_font_family(os.path.join(output_dir, f"{scenario_base_name}_VC_{tp}.html"))
            generate_vc_plot(compare_vc_gdf, tp, 100, os.path.join(output_dir, f"{scenario_compare_name}_VC_{tp}.html"))
            insert_jp_ui_font_family(os.path.join(output_dir, f"{scenario_compare_name}_VC_{tp}.html"))

            generate_cspd_plot(base_vc_gdf, tp, 1, os.path.join(output_dir, f"{scenario_base_name}_CSPD_{tp}.html"))
            insert_jp_ui_font_family(os.path.join(output_dir, f"{scenario_base_name}_CSPD_{tp}.html"))
            generate_cspd_plot(compare_vc_gdf, tp, 1, os.path.join(output_dir, f"{scenario_compare_name}_CSPD_{tp}.html"))
            insert_jp_ui_font_family(os.path.join(output_dir, f"{scenario_compare_name}_CSPD_{tp}.html"))

        con.close()
        print(f"Finished generating maps for {scenario_base_name} vs {scenario_compare_name}!")
