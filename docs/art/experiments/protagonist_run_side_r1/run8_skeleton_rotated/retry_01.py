"""Regenerate the detached far hand on frame 01 by requesting its full pose."""
from run_advisor import OUT,request_body,main


def first_pose():
    request=request_body()
    request["keypoints"]=[request["keypoints"][0]]*3
    request["seed"]+=1
    return request


if __name__=="__main__":
    directory=OUT/"retry_01"
    directory.mkdir(exist_ok=True)
    main(directory,first_pose,(1,2,3))

