"""Second draw of frame 02; the first candidates broke the folded leg."""
from regenerate import HERE,targets,main


def down():
    req=targets()
    req["keypoints"]=[req["keypoints"][0]]*3
    req["seed"]+=1
    req["action"]="running, compression with one forefoot planted and the other lower leg folded behind, both bare feet visible"
    return req


if __name__=="__main__":
    out=HERE/"retry_down"
    out.mkdir(exist_ok=True)
    main(out,down,(1,2,3))
