"""Room 1 v1. Metres; O at outer front-left; +Y toward rear door."""
PARAMETERS = {
 'RoomWidth':(20.0,'PROVISIONAL','房间外包宽度'),
 'RoomDepth':(9.5,'PROVISIONAL','房间外包深度'),
 'Wall':(.2,'PROVISIONAL','墙厚'),
 'PodWidth':(1.05,'PROVISIONAL','单舱最大外包宽'),
 'PodLength':(2.3,'BASELINE','单舱最大外包长'),
 'PodHeight':(1.0,'PROVISIONAL','单舱高度'),
 'Gap':(.7,'TARGET','相邻舱长边操作净间距'),
 'LongAisle':(1.6,'BASELINE','中央纵向通道净宽'),
 'CrossAisle':(3.5,'BASELINE','中央横向通道净宽'),
 'DoorWidth':(1.6,'PROVISIONAL','后墙中央门净宽'),
 'BaseChamfer':(.12,'PROVISIONAL','底座平面倒角'),
 'BodyInset':(.04,'PROVISIONAL','主体每侧内收'),
 'LidInset':(.06,'PROVISIONAL','舱盖每侧内收'),
 'WindowInset':(.16,'PROVISIONAL','观察区横向内收'),
 'WindowLength':(.50,'PROVISIONAL','头部观察区长度'),
 'WindowEndInset':(.18,'PROVISIONAL','观察区距头端'),
 'PanelWidth':(.30,'PROVISIONAL','壁面认证面板宽'),
 'PanelDepth':(.05,'PROVISIONAL','壁面面板突出深度'),
 'PanelOffset':(.20,'PROVISIONAL','面板距门洞侧缘'),
 'CutWallHeight':(1.3,'DISPLAY ONLY','3D剖切显示墙高，不是净高'),
}

def layout(overrides=None):
 v={k:a[0] for k,a in PARAMETERS.items()};v.update(overrides or {})
 v['InnerWidth']=v['RoomWidth']-2*v['Wall'];v['InnerDepth']=v['RoomDepth']-2*v['Wall']
 v['BlockWidth']=5*v['PodWidth']+4*v['Gap']
 v['SideMargin']=(v['InnerWidth']-v['LongAisle']-2*v['BlockWidth'])/2
 v['EndMargin']=(v['InnerDepth']-v['CrossAisle']-2*v['PodLength'])/2
 pods=[]
 for row in range(2):
  y=v['Wall']+v['EndMargin']+row*(v['PodLength']+v['CrossAisle'])
  for side in range(2):
   x0=v['Wall']+v['SideMargin']+side*(v['BlockWidth']+v['LongAisle'])
   for col in range(5):
    pods.append(dict(id=f'P{row*10+side*5+col+1:02}',row=row,side=side,col=col,
                     x=x0+col*(v['PodWidth']+v['Gap']),y=y,w=v['PodWidth'],d=v['PodLength'],h=v['PodHeight'],head='front' if row==0 else 'rear'))
 return v,pods

def validate(v,pods):
 def near(a,b):return abs(a-b)<1e-8
 pairs=[]
 for i,a in enumerate(pods):
  for b in pods[i+1:]:
   if min(a['x']+a['w'],b['x']+b['w'])>max(a['x'],b['x'])+1e-8 and min(a['y']+a['d'],b['y']+b['d'])>max(a['y'],b['y'])+1e-8:pairs.append([a['id'],b['id']])
 assert len(pods)==20 and not pairs
 assert v['SideMargin']>0 and v['EndMargin']>0
 # Test actual envelope spacing, including central axes and all four walls.
 rear=[p for p in pods if p['row']==1];front=[p for p in pods if p['row']==0]
 long=min(p['x'] for p in pods if p['side']==1)-max(p['x']+p['w'] for p in pods if p['side']==0)
 cross=min(p['y'] for p in rear)-max(p['y']+p['d'] for p in front)
 gap=min(b['x']-a['x']-a['w'] for a,b in zip(pods,pods[1:]) if a['row']==b['row'] and a['side']==b['side'])
 assert near(long,v['LongAisle']) and near(cross,v['CrossAisle']) and near(gap,v['Gap'])
 return dict(pod_count=20,quadrant_counts=[5,5,5,5],envelope_m=[v['RoomWidth'],v['RoomDepth']],
   interior_clear_m=[v['InnerWidth'],v['InnerDepth']],pod_envelope_m=[v['PodWidth'],v['PodLength'],v['PodHeight']],
   longitudinal_aisle_clear_m=long,cross_aisle_clear_m=cross,min_long_side_gap_m=gap,
   left_wall_margin_m=min(p['x'] for p in pods)-v['Wall'],
   right_wall_margin_m=v['RoomWidth']-v['Wall']-max(p['x']+p['w'] for p in pods),
   front_wall_margin_m=min(p['y'] for p in pods)-v['Wall'],
   rear_wall_margin_m=v['RoomDepth']-v['Wall']-max(p['y']+p['d'] for p in pods),
   entrance_buffer_m=v['EndMargin'],entrance_buffer_definition='后墙内面至后排舱头端的空置带；不是独立回转前室',
   door_clear_width_m=v['DoorWidth'],door_axis_offset_m=0.0,door_count=1,
   envelope_collisions=pairs,static_fit_passed=True)
