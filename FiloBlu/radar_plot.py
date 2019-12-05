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
                    'Atti respiratori'     : lambda x : (x - 10) / (70  - 10) * 100,
                    'Glicemia'             : lambda x : (x - 50) / (220 - 50) * 100,
                    'Sistolica (max)'      : lambda x : (x - 90) / (140 - 90) * 100,
                    'Diastolica (min)'     : lambda x : (x - 50) / (200 - 50) * 100,
                    'Frequenza'            : lambda x : (x - 50) / (200 - 50) * 100,
                    'Saturazione'          : lambda x : (x -  0) / (100 -  0) * 100,
                    'Temperatura'          : lambda x : (x - 35) / (40  - 35) * 100
                  }

bio_labels = {
              'Atti respiratori' : 'Atti\nrespiratori',      # 10 - 70
              'Glicemia'         : 'Glicemia' ,              # 50 - 220
              'Sistolica (max)'  : 'Pressione\nSistolica',   # 90 - 140
              'Diastolica (min)' : 'Pressione\nDiastolica',  # 90 - 140
              'Frequenza'        : 'Frequenza\ncardiaca',    # 50 - 200
              'Temperatura'      : 'Temperatura\ncorporea',  # 35 -  45
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

  ax.set_rgrids([20, 40, 60, 80])

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

      ax.plot(theta, params.values(), '-o', color=color, alpha=.75)
      ax.fill(theta, params.values(), facecolor=color, alpha=.25)
      ax.set_varlabels([bio_labels[k] for k in params.keys()])


      if id_patient:
        fig.savefig(os.path.join(IMAGE_DESTINATION_PATH,
                                 'patient_' + str(id_patient)) + '.png',
                    #transparency=True,
                    bbox_inches='tight')
      ax.cla()


if __name__ == '__main__':

  import json

  bio_params = {
                'Diastolica (min)'     :  95,
                'Atti respiratori'     :  42,
                'Frequenza'            :  64,
                'Temperatura'          : 37.3,
                'Sistolica (max)'      : 124,
                'Glicemia'             : 200,
                'Saturazione'          : 15
                }

  radar_plot([bio_params], ['filoblu'], title=True)

  processed = {k : std_bio_params[k](v) if v else np.nan for k, v in bio_params.items()}

  print('Processed bio-parameters:')
  print(json.dumps(processed, indent = 4))
