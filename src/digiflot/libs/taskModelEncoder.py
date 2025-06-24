import json
import pathlib
import pandas as pd
import numpy as np

try:
    from libs import taskModel, dahengCamModel, atlasSensor, lidar, raspiCamModel
except:
    from . import taskModel, dahengCamModel, atlasSensor, lidar, raspiCamModel

class TaskModelEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, pd.DataFrame):
            return obj.to_dict(orient="records")
        if isinstance(obj, pathlib.Path):
            return str(obj)
        if isinstance(obj, np.int32) or isinstance(obj, np.int64) or isinstance(obj, np.uint8):
            return str(int(obj))
        if isinstance(obj, taskModel.TaskModel):
            my_dict = obj.__dict__.copy()
            my_dict["currentstagetype"] = obj.currentstagetype
            my_dict["currentstagename"] = obj.currentstagename            
            return my_dict 
        if isinstance(obj, raspiCamModel.RaspiCamModel):
            my_dict = obj.__dict__.copy()
            my_dict.pop("taskModel", None)
            return my_dict
        if isinstance(obj, dahengCamModel.DahengCamModel):
            my_dict = obj.__dict__.copy()
            my_dict.pop("taskModel", None)
            return my_dict
        if isinstance(obj, atlasSensor.AtlasSensor) or isinstance(obj, lidar.Lidar):
            return obj.__dict__
        return ""       