import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib_scalebar.scalebar import ScaleBar

# 中文字體設定
plt.rcParams['font.family'] = 'Microsoft JhengHei'
plt.rcParams['axes.unicode_minus'] = False

# ====== Step 1：讀取資料 ======
# 古蹟資料（Excel）
df = pd.read_excel('文化資產複合查詢.xlsx')
df_expanded = df.assign(所在地理區域=df['所在地理區域'].str.split(',')).explode('所在地理區域')
df_expanded['所在地理區域'] = df_expanded['所在地理區域'].str.strip()

# 各區古蹟數量統計
area_counts = df_expanded.groupby('所在地理區域').size().reset_index(name='古蹟數量')

# ====== Step 2：讀取 shapefile 並篩選台南 ======
tainan_gdf = gpd.read_file("鄉(鎮、市、區)界線1140318/TOWN_MOI_1140318.shp", encoding='utf-8')
tainan_gdf = tainan_gdf[tainan_gdf['COUNTYNAME'] == '臺南市'].copy()

# 建立「臺南市 + 行政區」的欄位，方便合併
tainan_gdf['所在地理區域'] = tainan_gdf['COUNTYNAME'] + tainan_gdf['TOWNNAME']

# ====== Step 3：合併古蹟數量資料 ======
tainan_gdf = tainan_gdf.merge(area_counts, on='所在地理區域', how='left')
tainan_gdf['古蹟數量'] = tainan_gdf['古蹟數量'].fillna(0)

# ====== Step 4：計算面積與密度 ======
tainan_gdf = tainan_gdf.to_crs(epsg=3826)  # 轉換為臺灣區域座標系 (TWD97 TM2)
tainan_gdf['面積(km2)'] = tainan_gdf['geometry'].area / 10**6
tainan_gdf['古蹟密度'] = tainan_gdf['古蹟數量'] / tainan_gdf['面積(km2)']

# ====== Step 5：畫地圖 1 - 古蹟數量 Choropleth Map ======
fig, ax = plt.subplots(figsize=(10, 10))
tainan_gdf.plot(
    column='古蹟數量',
    cmap='OrRd',
    linewidth=0.8,
    edgecolor='black',
    legend=True,
    scheme='user_defined',
    classification_kwds={'bins': [1, 5, 10, 20, 40, 60]},
    ax=ax
)
ax.set_title('臺南市各行政區古蹟數量著色圖', fontsize=16)
ax.axis('off')

# 加比例尺
scalebar = ScaleBar(1, units="m", location='lower right')
ax.add_artist(scalebar)

# ====== Step 6：畫地圖 2 - 古蹟密度 Choropleth Map ======
# 效果不佳，用途也不明顯
# 已棄用，未在報告中使用
fig, ax = plt.subplots(figsize=(10, 10))
tainan_gdf['log密度'] = np.log1p(tainan_gdf['古蹟密度'])
tainan_gdf.plot(
    column='log密度',
    cmap='YlGnBu',
    linewidth=0.8,
    edgecolor='black',
    legend=True,
    scheme='quantiles',
    k=5,
    ax=ax
)
ax.set_title('臺南市古蹟密度著色圖（每平方公里）', fontsize=16)
ax.axis('off')

# 比例尺
scalebar = ScaleBar(1, units="m", location='lower right')
ax.add_artist(scalebar)

# ====== Step 7：畫地圖 3 - 臺南市區界圖 ======
# 根據投影座標系 (EPSG:3826) 設定範圍來裁切
# 以輸出西南方古蹟數量較高的區域
minx, miny, maxx, maxy = 160000, 2500000, 180000, 2553000

# 用 bbox 篩選
bbox = (tainan_gdf.geometry.centroid.x >= minx) & (tainan_gdf.geometry.centroid.x <= maxx) & \
       (tainan_gdf.geometry.centroid.y >= miny) & (tainan_gdf.geometry.centroid.y <= maxy)

tainan_subset = tainan_gdf[bbox]

# 畫出裁切後的區域邊界
fig, ax = plt.subplots(figsize=(8, 8))
tainan_subset.boundary.plot(ax=ax, edgecolor='red', linewidth=1.5)

ax.set_axis_off()
plt.show()