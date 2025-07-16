import os
import duckdb
import geopandas as gpd
import numpy as np
import pandas as pd
import codecs
from shapely import from_wkb

import lonboard as lb
from lonboard import Map, PathLayer, basemap
from lonboard.colormap import apply_categorical_cmap
from lonboard.layer_extension import PathStyleExtension

import warnings

warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)
warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning)


def decode_escaped_wkb(s):
    s_fixed = s.replace('\\X', '\\x')  # fix uppercase \X to \x
    # Decode escape sequences to bytes
    wkb_bytes = codecs.decode(s_fixed, 'unicode_escape').encode('latin1')
    return from_wkb(wkb_bytes)


def create_gdf_using_decoded_geoms(input_df):
    input_df['geometry'] = input_df['geometry'].apply(decode_escaped_wkb)
    gdf_output = gpd.GeoDataFrame(input_df, geometry='geometry')
    return gdf_output


def categorise_vol_diff(diff):
    if diff < 0:
        return [255, 128, 0]
    else:
        return [0, 204, 204]


def categorise_cap_diff(diff):
    if diff < 0:
        return [255, 56, 76]
    else:
        return [64, 132, 234]


def categorise_vc(vc):
    if vc < 0.6:
        return [26, 150, 65]
    elif vc < 0.7:
        return [138, 204, 98]
    elif vc < 0.8:
        return [219, 240, 158]
    elif vc < 0.9:
        return [254, 223, 154]
    elif vc < 1.0:
        return [245, 144, 83]
    elif vc < 1.2:
        return [215, 25, 28]
    else:
        return [138, 0, 5]


def categorise_speed(cspd):
    if cspd < 10:
        return [0, 0, 0]
    elif cspd < 20:
        return [133, 11, 3]
    elif cspd < 30:
        return [245, 19, 2]
    elif cspd < 40:
        return [245, 107, 2]
    elif cspd < 60:
        return [245, 200, 2]
    elif cspd < 80:
        return [140, 245, 2]
    else:
        return [0, 194, 45]


def categorise_lanes(lanes):
    if abs(lanes) < 1:
        return [0, 0, 0, 0]
    elif abs(lanes) < 2:
        return [255, 56, 76, 255]
    elif abs(lanes) < 3:
        return [255, 145, 0, 255]
    elif abs(lanes) < 4:
        return [255, 210, 0, 255]
    elif abs(lanes) < 5:
        return [120, 163, 0, 255]
    elif abs(lanes) < 6:
        return [174, 105, 255, 255]
    else:
        return [64, 132, 234, 255]


def generate_volume_diff_plot(gdf_input, plot_column, min_abs_vol, file_name):
    scale = 400 / gdf_input[plot_column].abs().max()
    gdf_input["color"] = gdf_input[plot_column].apply(categorise_vol_diff)

    # sort data so that small abs values get plotted first
    gdf = gdf_input
    gdf[plot_column + "_abs"] = gdf[plot_column].abs()
    gdf[plot_column] = gdf[plot_column].round()
    gdf = gdf.query(f"{plot_column}_abs >= {min_abs_vol}")
    gdf = gdf.sort_values(plot_column + "_abs")
    # define lonboard extensions
    path_style_ext = PathStyleExtension(offset=True)
    # define styles
    line_widths = gdf[plot_column].abs().to_numpy()
    line_colors = np.vstack(gdf["color"].values).astype(np.uint8)
    road_layer = PathLayer.from_geopandas(
        gdf_input[['A', 'B', 'geometry']],
        width_min_pixels=0.5,
        get_color=[168, 168, 168],
        auto_highlight=False,
        pickable=False,
    )
    diff_layer = PathLayer.from_geopandas(
        gdf[['A', 'B', 'geometry', plot_column]],
        width_min_pixels=0,
        width_max_pixels=10000,
        get_color=line_colors,
        get_width=line_widths,
        width_scale=scale,
        cap_rounded=True,
        extensions=[path_style_ext],
        get_offset=-0.7,
        auto_highlight=True,
        pickable=True,
        opacity=0.85
    )
    view_state = {
        "longitude": 144.935032,
        "latitude": -37.839289,
        "zoom": 9,
    }
    m = Map(layers=[diff_layer, road_layer], basemap_style=basemap.CartoBasemap.DarkMatter, view_state=view_state,
            show_tooltip=True, _height=900)
    m.to_html(file_name, title=file_name)
    # close_all is required so that when we iteratively save the map
    # the state of `Map` doesn't get carried over to the next one
    # which would cause the saved HTML to become larger and larger.
    Map.close_all()


def generate_network_diff_plot(gdf_input, plot_column, min_abs_vol, file_name):
    gdf_input.loc[
        (
                ((gdf_input[plot_column] > 9999) & (gdf_input["LINKC_AM"] == 25)) |
                ((gdf_input[plot_column] > 9999) & (gdf_input["LINKC_AM"] == 5)) |
                ((gdf_input[plot_column] > 9999) & (gdf_input["LINKC_AM"] == 16))
        ),
        plot_column
    ] = 1000
    gdf_input.loc[
        (
                ((gdf_input[plot_column] < -9999) & (gdf_input["LINKC_AM"] == 25)) |
                ((gdf_input[plot_column] < -9999) & (gdf_input["LINKC_AM"] == 5)) |
                ((gdf_input[plot_column] < -9999) & (gdf_input["LINKC_AM"] == 16))
        ),
        plot_column
    ] = -1000
    scale = 350 / gdf_input[plot_column].abs().max()
    gdf_input["color"] = gdf_input[plot_column].apply(categorise_cap_diff)

    # sort data so that small abs values get plotted first
    gdf = gdf_input
    gdf[plot_column + "_abs"] = gdf[plot_column].abs()
    gdf[plot_column] = gdf[plot_column].round()
    gdf = gdf.query(f"{plot_column}_abs >= {min_abs_vol}")
    gdf = gdf.sort_values(plot_column + "_abs")
    # define lonboard extensions
    path_style_ext = PathStyleExtension(offset=True)
    # define styles
    line_widths = gdf[plot_column].abs().to_numpy()
    line_widths = line_widths.astype(np.float64)
    line_colors = np.vstack(gdf["color"].values).astype(np.uint8)
    road_layer = PathLayer.from_geopandas(
        gdf_input[['A', 'B', 'geometry']],
        width_min_pixels=0.5,
        get_color=[168, 168, 168],
        auto_highlight=False,
        pickable=False,
    )
    diff_layer = PathLayer.from_geopandas(
        gdf[['A', 'B', 'geometry', plot_column]],
        width_min_pixels=0.001,
        width_max_pixels=10000,
        get_color=line_colors,
        get_width=line_widths,
        width_scale=scale,
        cap_rounded=True,
        extensions=[path_style_ext],
        get_offset=-0.7,
        auto_highlight=True,
        pickable=True,
        opacity=0.85,
        width_units='meters'
    )
    view_state = {
        "longitude": 144.935032,
        "latitude": -37.839289,
        "zoom": 9,
    }
    m = Map(layers=[diff_layer, road_layer], basemap_style=basemap.CartoBasemap.DarkMatter, view_state=view_state,
            show_tooltip=True, _height=900)
    m.to_html(file_name, title=file_name)
    # close_all is required so that when we iteratively save the map
    # the state of `Map` doesn't get carried over to the next one
    # which would cause the saved HTML to become larger and larger.
    Map.close_all()


def generate_vc_plot(gdf_input, time_period, min_abs_vol, file_name):
    scale = 400 / gdf_input[f"VEH_{time_period}"].abs().max()
    gdf_input["color"] = gdf_input[f"VC_{time_period}"].apply(categorise_vc)

    # sort data so that small abs values get plotted first
    gdf = gdf_input
    gdf[f"VEH_{time_period}" + "_abs"] = gdf[f"VEH_{time_period}"].abs()
    gdf[f"VEH_{time_period}"] = gdf[f"VEH_{time_period}"].round()
    gdf = gdf.query(f"VEH_{time_period}_abs >= {min_abs_vol}")
    gdf = gdf.sort_values(f"VEH_{time_period}" + "_abs")
    # define lonboard extensions
    path_style_ext = PathStyleExtension(offset=True)
    # define styles
    line_widths = gdf[f"VEH_{time_period}"].abs().to_numpy()
    line_colors = np.vstack(gdf["color"].values).astype(np.uint8)
    road_layer = PathLayer.from_geopandas(
        gdf_input[['A', 'B', 'geometry']],
        width_min_pixels=0.5,
        get_color=[168, 168, 168],
        auto_highlight=False,
        pickable=False,
    )
    vc_layer = PathLayer.from_geopandas(
        gdf[['A', 'B', 'geometry', f"VC_{time_period}", f"VEH_{time_period}"]],
        width_min_pixels=0,
        width_max_pixels=10000,
        get_color=line_colors,
        get_width=line_widths,
        width_scale=scale,
        cap_rounded=True,
        extensions=[path_style_ext],
        get_offset=-0.7,
        auto_highlight=True,
        pickable=True,
        opacity=0.85
    )
    view_state = {
        "longitude": 144.935032,
        "latitude": -37.839289,
        "zoom": 9,
    }
    m = Map(layers=[vc_layer, road_layer], basemap_style=basemap.CartoBasemap.Positron, view_state=view_state,
            show_tooltip=True, _height=900)
    m.to_html(file_name, title=file_name)
    # close_all is required so that when we iteratively save the map
    # the state of `Map` doesn't get carried over to the next one
    # which would cause the saved HTML to become larger and larger.
    Map.close_all()


def generate_cspd_plot(gdf_input, time_period, min_abs_vol, file_name):
    gdf_input["color"] = gdf_input[f"CSPD_{time_period}"].apply(categorise_speed)
    gdf_input["width"] = 15
    # sort data so that small abs values get plotted first
    gdf = gdf_input
    gdf[f"CSPD_{time_period}" + "_abs"] = gdf[f"CSPD_{time_period}"].abs()
    gdf[f"CSPD_{time_period}"] = gdf[f"CSPD_{time_period}"].round()
    gdf = gdf.sort_values(f"CSPD_{time_period}" + "_abs")
    gdf = gdf.query(f"VEH_{time_period}_abs >= {min_abs_vol}")
    # define lonboard extensions
    path_style_ext = PathStyleExtension(offset=True)
    # define styles
    line_widths = gdf["width"].abs().to_numpy()
    line_colors = np.vstack(gdf["color"].values).astype(np.uint8)
    road_layer = PathLayer.from_geopandas(
        gdf_input[['A', 'B', 'geometry']],
        width_min_pixels=0.5,
        get_color=[168, 168, 168],
        auto_highlight=False,
        pickable=False,
    )
    cspd_layer = PathLayer.from_geopandas(
        gdf[['A', 'B', 'geometry', f"CSPD_{time_period}"]],
        width_min_pixels=2,
        width_max_pixels=8,
        get_color=line_colors,
        get_width=line_widths,
        # width_scale=line_widths,
        cap_rounded=True,
        extensions=[path_style_ext],
        get_offset=-0.7,
        auto_highlight=True,
        pickable=True,
        opacity=0.85
    )
    view_state = {
        "longitude": 144.935032,
        "latitude": -37.839289,
        "zoom": 9,
    }
    m = Map(layers=[cspd_layer, road_layer], basemap_style=basemap.CartoBasemap.Positron, view_state=view_state,
            show_tooltip=True, _height=900)
    m.to_html(file_name, title=file_name)
    # close_all is required so that when we iteratively save the map
    # the state of `Map` doesn't get carried over to the next one
    # which would cause the saved HTML to become larger and larger.
    Map.close_all()


def generate_nlanes_plot(gdf_input, plot_col, min_abs_vol, file_name):
    gdf_input[plot_col + "_abs"] = gdf_input[plot_col].abs()
    gdf_input["color"] = gdf_input[plot_col + "_abs"].apply(categorise_lanes)
    gdf_input["width"] = 15
    # sort data so that small abs values get plotted first
    gdf = gdf_input
    gdf[plot_col] = gdf[plot_col].round()
    gdf = gdf.sort_values(plot_col + "_abs")
    gdf = gdf.query(f"{plot_col}_abs >= {min_abs_vol}")
    # define lonboard extensions
    path_style_ext = PathStyleExtension(offset=True)
    # define styles
    line_widths = gdf["width"].abs().to_numpy()
    line_colors = np.vstack(gdf["color"].values).astype(np.uint8)
    road_layer = PathLayer.from_geopandas(
        gdf_input[['A', 'B', 'geometry']],
        width_min_pixels=0.5,
        get_color=[168, 168, 168],
        auto_highlight=False,
        pickable=False,
    )
    lanes_layer = PathLayer.from_geopandas(
        gdf[['A', 'B', 'geometry', plot_col]],
        width_min_pixels=2,
        width_max_pixels=8,
        get_color=line_colors,
        get_width=line_widths,
        # width_scale=line_widths,
        cap_rounded=True,
        extensions=[path_style_ext],
        get_offset=-0.7,
        auto_highlight=True,
        pickable=True,
        opacity=0.85
    )
    view_state = {
        "longitude": 144.935032,
        "latitude": -37.839289,
        "zoom": 9,
    }
    m = Map(layers=[lanes_layer, road_layer], basemap_style=basemap.CartoBasemap.Positron, view_state=view_state,
            show_tooltip=True, _height=900)
    m.to_html(file_name, title=file_name)
    # close_all is required so that when we iteratively save the map
    # the state of `Map` doesn't get carried over to the next one
    # which would cause the saved HTML to become larger and larger.
    Map.close_all()


def insert_jp_ui_font_family(html_file_path):
    style_block = """
<style>
  :root {
    --jp-ui-font-family: "VIC", monospace;
  }
</style>
"""
    with open(html_file_path, 'r', encoding='utf-8') as f:
        html = f.read()

    if '<head>' in html:
        # Insert style block right after <head>
        new_html = html.replace('<head>', f'<head>{style_block}')
    else:
        # If no <head>, add style block at start
        new_html = style_block + html

    with open(html_file_path, 'w', encoding='utf-8') as f:
        f.write(new_html)
