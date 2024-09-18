# coding:utf-8
import yaml
import os


class Cfg():
    def __init__(self):
        curPath = os.path.dirname(os.path.realpath(__file__))
        yamlPath = os.path.join(curPath, "config.yaml")
        f = open(yamlPath, 'r', encoding='utf-8')
        cfg_f = f.read()
        d =  yaml.safe_load(cfg_f)
        
        for k in d:
            setattr(self,k,d[k])

cfg = Cfg()
