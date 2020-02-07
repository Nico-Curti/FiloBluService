#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, RegularPolygon
from matplotlib.path import Path
from matplotlib.projections.polar import PolarAxes
from matplotlib.projections import register_projection
from matplotlib.spines import Spine
from matplotlib.transforms import Affine2D

__author__ = 'Nico Curti'
__email__ = 'nico.curti2@unibo.it'


IMAGE_DESTINATION_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'img'))


std_bio_params = {
                    'Atti respiratori'     : lambda x : (5*x - 50) / 100,
                    'Glicemia'             : lambda x : (0.5*x - 0) / 100,
                    'Sistolica (max)'      : lambda x : (0.5*x - 0) / 100,
                    'Diastolica (min)'     : lambda x : (0.937*x - 3.125) / 100,
                    'Frequenza'            : lambda x : (0.625*x + 6.25) / 100,
                    'Saturazione'          : lambda x : (5*x - 400) / 100,
                    'Temperatura'          : lambda x : (12.5*x - 412.5) / 100
                  }

std_bio_thick = {#here thicks for standard plot from radar_filo script
                    'Atti respiratori'     : [15, 20, 25, 30],
                    'Glicemia'             : [50, 100, 150, 200],
                    'Sistolica (max)'      : [50, 100, 150, 200],
                    'Diastolica (min)'     : [30, 60, 90, 110],
                    'Frequenza'            : [30, 70, 110, 150],
                    'Saturazione'          : [85, 90, 95, 100],
                    'Temperatura'          : [35, 37, 39, 41]
                  }

bio_labels = {
              'Atti respiratori' : 'Atti\nrespiratori',      # 10 - 70
              'Glicemia'         : '\n\nGlicemia\n'+5*''+'(mg/dl)' ,              # 50 - 220
              'Sistolica (max)'  : 'Pressione\nSistolica\n'+1*' '+ '(mmhg)',   # 90 - 140
              'Diastolica (min)' : 'Pressione\nDiastolica\n'+1*' '+ '(mmhg)',  # 90 - 140
              'Frequenza'        : 'Frequenza\ncardiaca\n'+2*' '+ '(bpm)'+'\n\n'+'',    # 50 - 200
              'Temperatura'      : '\nTemperatura\ncorporea\n'+5*''+'(°C)',  # 35 -  45
              'Saturazione'      : 'Saturazione\nossigeno'   # 0  - 100
              }


def radar_factory(num_vars, frame='circle'):
  """Create a radar chart with `num_vars` axes.

  This function creates a RadarAxes projection and registers it.

  Parameters
  ----------
  num_vars : int
      Number of variables for radar chart.
  frame : {'circle' | 'polygon'}
      Shape of frame surrounding axes.

  """
  # calculate evenly-spaced axis angles
  theta = np.linspace(0, 2*np.pi, num_vars, endpoint=False)

  class RadarAxes(PolarAxes):

    name = 'radar'
    # use 1 line segment to connect specified points
    RESOLUTION = 1

    def __init__(self, *args, **kwargs):
      super().__init__(*args, **kwargs)
      # rotate plot such that the first axis is at the top
      self.set_theta_zero_location('N')

    def fill(self, closed=True, *args, **kwargs):
      """Override fill so that line is closed by default"""
      return super().fill(closed=closed, *args, **kwargs)

    def plot(self, *args, **kwargs):
      """Override plot so that line is closed by default"""
      lines = super().plot(*args, **kwargs)
      for line in lines:
        self._close_line(line)

    def _close_line(self, line):
      x, y = line.get_data()
      # FIXME: markers at x[0], y[0] get doubled-up
      if x[0] != x[-1]:
        x = np.concatenate((x, [x[0]]))
        y = np.concatenate((y, [y[0]]))
        line.set_data(x, y)

    def set_varlabels(self, labels):
      self.set_thetagrids(np.degrees(theta), labels,
                          fontsize=16,
                          fontweight='semibold')

    def _gen_axes_patch(self):
      # The Axes patch must be centered at (0.5, 0.5) and of radius 0.5
      # in axes coordinates.
      if frame == 'circle':
        return Circle((0.5, 0.5), 0.5)
      elif frame == 'polygon':
        return RegularPolygon((0.5, 0.5), num_vars,
                                radius=.5, edgecolor="k")
      else:
        raise ValueError("unknown value for 'frame': %s" % frame)

    def _gen_axes_spines(self):
      if frame == 'circle':
        return super()._gen_axes_spines()
      elif frame == 'polygon':
        # spine_type must be 'left'/'right'/'top'/'bottom'/'circle'.
        spine = Spine(axes=self,
                      spine_type='circle',
                      path=Path.unit_regular_polygon(num_vars))
        # unit_regular_polygon gives a polygon of radius 1 centered at
        # (0, 0) but we want a polygon of radius 0.5 centered at (0.5,
        # 0.5) in axes coordinates.
        spine.set_transform(Affine2D().scale(.5).translate(.5, .5)
                            + self.transAxes)
        return {'polar': spine}
      else:
        raise ValueError("unknown value for 'frame': %s" % frame)

  register_projection(RadarAxes)
  return theta


def radar_plot(bio_params, patient_names=None, title=True):

  theta = radar_factory(len(std_bio_params), frame='polygon')
  color = 'royalblue'

  fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(8, 8),
                         subplot_kw=dict(projection='radar'))
  # one ax for every param
  axes_list = [ax.figure.add_axes(ax.get_position(), projection='polar', 
               label='twin'+str(1), frameon=False,
               theta_direction=ax.get_theta_direction(),
               theta_offset=ax.get_theta_offset()) for i in range(len(std_bio_params))]
  
  
  
  asd=bio_params[0]
  tmp=list(asd.keys())
  
  angles = dict(zip(tmp, theta*180/np.pi))#assign correct angle (not in order)
  ax.set_rgrids([0,0.25,0.50,0.75,1],labels=['','','','',''],angle=1)# to mask current axis
  ax.set_ylim(0,1)
  
  for k,key in zip(range(len(asd)),bio_params[0]):
      
      
      axes_list[k].set_rgrids([0.25,0.50,0.75,1],labels=np.round((np.array(std_bio_thick[key]))),angle=angles[key],fontsize=11,
                              fontweight='semibold')
      axes_list[k].xaxis.set_visible(False)
      axes_list[k].set_ylim(0,1)

   
  uniques_patient = set()


  for id_patient, bio_param in zip(patient_names, bio_params):

    if bio_param is not None and id_patient not in uniques_patient:

      uniques_patient.add(id_patient)

      if 'storage_time' in bio_param:
        bio_time = bio_param['storage_time']
        bio_param.pop('storage_time', None)
      else:
        bio_time = None

      params = {k : std_bio_params[k](v) if v else 0
                for k, v in bio_param.items()}

      for k in std_bio_params.keys():
        if k not in params:
          params[k] = 0

      if title and id_patient:
        img_title = 'Paziente ' + str(id_patient)
        img_title += ' : ' + bio_time.strftime("%m/%d/%Y, %H:%M:%S") if bio_time else ''
        ax.set_title(img_title,
                     weight='bold', size=24,
                     position=(0.5, 1.1),
                     horizontalalignment='center',
                     verticalalignment='center')

      ax.plot(theta, list(params.values()), '-o', color=color, alpha=.75)
      #ax.fill(list(theta), list(params.values()), facecolor=color, alpha=.25)
      ax.set_varlabels([bio_labels[k] for k in params.keys()])

      #plt.show()#show in console  
      if id_patient:
        fig.savefig(os.path.join(IMAGE_DESTINATION_PATH,
                                 'patient_' + str(id_patient)) + '.png',
                    #transparency=True,
                    bbox_inches='tight')
      ax.cla()


if __name__ == '__main__':

  import json

  bio_params = {
                'Diastolica (min)'     :  60,
                'Atti respiratori'     :  30,
                'Frequenza'            :  100,
                'Temperatura'          : 37,
                'Sistolica (max)'      : 110,
                'Glicemia'             : 200,
                'Saturazione'          : 99
                }

  radar_plot([bio_params], ['filoblu'], title=True)

  processed = {k : std_bio_params[k](v) if v else np.nan for k, v in bio_params.items()}

  print('Processed bio-parameters:')
  print(json.dumps(processed, indent = 4))
