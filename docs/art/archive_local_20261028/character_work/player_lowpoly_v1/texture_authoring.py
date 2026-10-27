"""Editable original pixel drafts, intentionally sparse; coordinates are bottom-up.
No external art, random noise, face marks, baked directional shadows, or image AI.
"""
import bpy
import json

PALETTES={
    'cloth':[(216,224,217),(193,209,205),(174,195,193),(233,237,226),(206,218,213)],
    'hair':[(34,46,56),(27,37,47),(45,61,73),(59,76,85),(39,53,65)],
    'skin':[(205,167,144),(190,149,130),(217,181,155),(198,158,138)],
}

def make_textures(root):
    images={};source={'status':'Original provisional pixel color drafts; replace after visual review',
        'origin':'bottom-left','palettes_srgb':PALETTES,'layers':{}}
    for kind,(w,h) in {'cloth':(128,256),'hair':(128,128),'skin':(128,128)}.items():
        grid=[[0]*w for _ in range(h)];ops=[]
        def rect(x,y,ww,hh,color):
            ops.append({'type':'rect','xywh':[x,y,ww,hh],'color':color})
            for yy in range(max(0,y),min(h,y+hh)):
                for xx in range(max(0,x),min(w,x+ww)):grid[yy][xx]=color
        def polygon(points,color):
            ops.append({'type':'polygon','points':points,'color':color})
            for yy in range(max(0,min(y for x,y in points)),min(h,max(y for x,y in points)+1)):
                for xx in range(max(0,min(x for x,y in points)),min(w,max(x for x,y in points)+1)):
                    px,py=xx+.5,yy+.5;inside=False
                    for a,b in zip(points,points[1:]+points[:1]):
                        if (a[1]>py)!=(b[1]>py) and px<(b[0]-a[0])*(py-a[1])/(b[1]-a[1])+a[0]:inside=not inside
                    if inside:grid[yy][xx]=color
        if kind=='cloth':
            # Broad quiet base, stepped folds placed at tension / drape transitions.
            for x,reach,lean in [(17,49,3),(36,67,-3),(55,34,2),(81,52,-4),(101,65,3),(117,32,-2)]:
                polygon([(x,4),(x+4,4),(x+4,17),(x+3,17),(x+3+lean,reach//2),
                         (x+2+lean,reach//2),(x+lean,reach),(x-1+lean,reach),(x,20)],1)
            polygon([(38,10),(42,10),(43,29),(46,29),(46,44),(44,44),(44,30),(41,30)],4)
            polygon([(73,9),(77,9),(77,27),(79,27),(79,41),(77,41),(77,28),(74,28)],3)
            rect(4,5,120,1,1);rect(4,7,120,1,4)
            # A quiet front opening seam from collar toward waist, not a stripe down the skirt.
            rect(64,99,1,45,1);rect(65,111,1,32,3)
            polygon([(49,99),(51,99),(54,110),(54,117),(53,117),(52,108)],4)
            polygon([(77,100),(79,100),(76,111),(76,118),(75,118),(75,110)],4)
            for left in (4,68):
                rect(left,157,56,2,1);rect(left,160,56,1,3)
                polygon([(left+7,176),(left+10,176),(left+12,187),(left+11,203),(left+9,203),(left+9,188)],4)
                polygon([(left+33,189),(left+36,189),(left+35,203),(left+34,219),(left+32,219),(left+33,202)],1)
                rect(left+17,161,2,12,4)
            rect(4,239,56,2,1);rect(4,250,56,1,3)
        elif kind=='hair':
            # Back curtain gets broad connected lock clusters, not individual strands.
            for x,lo,hi in [(13,55,101),(34,49,114),(58,54,109),(76,54,95)]:
                polygon([(x,lo),(x+6,lo),(x+6,lo+11),(x+8,lo+11),(x+8,hi-14),
                         (x+6,hi-14),(x+6,hi),(x+3,hi),(x+3,hi-18),(x+1,hi-18)],2)
            polygon([(40,87),(43,87),(43,96),(46,96),(46,110),(44,110),(44,101),(41,101)],3)
            polygon([(64,59),(67,59),(67,77),(69,77),(69,92),(67,92),(67,81),(65,81)],4)
            for x in (7,26,49,87):
                polygon([(x,49),(x+2,49),(x+2,66),(x+4,66),(x+4,86),(x+2,86),(x+2,68),(x,68)],1)
            # Crown patches follow the curved silhouette; low contrast.
            polygon([(20,19),(26,19),(26,22),(32,22),(32,29),(29,29),(29,34),(22,34),(22,27),(20,27)],2)
            polygon([(31,29),(38,29),(38,34),(35,34),(35,37),(28,37),(28,34),(31,34)],3)
            polygon([(45,8),(49,8),(49,15),(53,15),(53,22),(50,22),(50,16),(45,16)],4)
            # Fringe and sidelocks share coherent long clusters.
            polygon([(87,13),(93,13),(93,20),(98,20),(98,29),(94,29),(94,25),(89,25)],2)
            for x in (100,116):
                polygon([(x,47),(x+2,47),(x+2,65),(x+3,65),(x+3,93),(x+2,93),(x+2,111),(x,111),(x,80)],2)
                rect(x+2,93,1,12,3)
        else:
            # Head UV remains absolutely featureless. Extremities use broad quiet blocks.
            rect(4,98,16,5,1);rect(5,105,2,7,3)
            rect(24,98,28,3,1);rect(25,102,4,3,3)
            rect(87,45,20,3,3)
        palette=PALETTES[kind]
        img=bpy.data.images.new(kind+'_draft',width=w,height=h,alpha=False)
        img.pixels.foreach_set([v for row in grid for index in row for v in tuple(c/255 for c in palette[index])+(1,)])
        img.filepath_raw=str(root/'textures'/f'{kind}_draft.png');img.file_format='PNG';img.save()
        path=img.filepath_raw;bpy.data.images.remove(img)
        img=bpy.data.images.load(path,check_existing=False);img.name='ORIGINAL_'+kind+'_DRAFT_REPLACEABLE'
        images[kind]=img
        source['layers'][kind]={'size':[w,h],'base_color_index':0,'operations':ops}
    (root/'texture_sources.json').write_text(json.dumps(source,indent=2),encoding='utf-8')
    return images
