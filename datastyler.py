import dataparser as oc
import pandas as pd
from matplotlib import *
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm, to_hex

gradientCMAP = LinearSegmentedColormap.from_list('rg', ["r", "w", "g"], N=256)


def BrEv_style(table, subset, nifty=0):
  a = list(table[subset].sort_values())
  for i in range(0,len(a)):
    if a[i] > nifty:
      nearestLow_BrEv, nearestHigh_BrEv = a[i-1], a[i]
      break
    else:
      continue
  return list((nearestLow_BrEv, nearestHigh_BrEv))


def background_with_norm(s, cmapCustom):
  cmap = colormaps.get_cmap(cmapCustom)
  norm = TwoSlopeNorm(vmin=-100.0, vcenter=0, vmax=100.0)
  return [
      'background-color: {:s}'.format(to_hex(c.flatten()))
      for c in cmap(norm(s.values))
  ]


def highlight_secondmax(val):
  is_max = val == val.max()
  is_second_max = val == val.nlargest(2).iloc[-1]
  color = ['background-color: gold' if m else '' for m in is_second_max]
  return color


def highlight_min_strike(val, nearestLow, nearestHigh, brev_put_min,
                         brev_put_max, brev_call_min, brev_call_max):
  if val in [nearestHigh, brev_put_max, brev_call_max]:
    return f"background: darkkhaki"
  elif val in [nearestLow, brev_put_min, brev_call_min]:
    return f"background: darksalmon"
  else:
    return f"background: white"


def prettier(df, index="NIFTY"):
  nifty = oc.niftyval(index)
  nifty = float("".join(map(str, nifty.split(','))))
  if index in ['NIFTY', 'FINNIFTY']:
    nearestLow = (nifty // 50) * 50
    nearestHigh = nearestLow + 50
  else:
    nearestLow = (nifty // 100) * 100
    nearestHigh = nearestLow + 100

  brev = []
  for each in ['Br-Ev_c', 'Br-Ev_p']:
    brev_min, brev_max = BrEv_style(table=df,
                                    subset=each,
                                    nifty=nifty)
    brev.append([brev_min, brev_max])

  styler = df.style.map(
      highlight_min_strike,
      nearestLow=nearestLow,
      nearestHigh=nearestHigh,
      brev_call_min=brev[0][0],
      brev_call_max=brev[0][1],
      brev_put_min=brev[1][0],
      brev_put_max=brev[1][1],
  )

  # styler = styler.set_properties(subset=[['OI_call','CHNG_OI_call','CHNG_OI_put','OI_put']], **{'width': '10px'})
  styler = styler.format(precision=1,
                         decimal='.').set_properties(**{
                             'text-align': 'center',
                             'padding': '7px'
                         })  #.applymap(highlight_strike, subset=["STRIKE"])
  styler = styler.bar(color="lightgreen",
                      subset=[
                          'CHNG_OI_c', 'openInterest_c', 'VOLUME_c',
                          'VOLUME_p', 'CHNG_OI_p', 'openInterest_p'
                      ])
  styler = styler.apply(highlight_secondmax,
                        axis=0).set_properties(**{
                            'border': '1.3px solid blue',
                            'color': 'black',
                            'border': '1.3px solid blue'
                        })
  styler = styler.set_table_styles([{
      'selector':
      'thead',
      'props':
      'background-color: powderblue; width: auto; border: 5px; position:sticky; top:0px; height: 50px; border: 5px #73AD21;overflow-x:auto; overflow-y:auto;'
  }])
  styler = styler.highlight_max(color='salmon', axis=0)
  gradientCMAP = LinearSegmentedColormap.from_list('rg', ["r", "w", "g"],
                                                   N=256)
  #styler = styler.background_gradient(subset=['%_call', '%_put'],
  #                                   cmap=gradientCMAP)

  styler = styler.apply(
      background_with_norm,
      cmapCustom=LinearSegmentedColormap.from_list('rg', ["r", "w", "g"],
                                                   N=256),
      subset=['%_c',
              '%_p']).set_properties(subset=[
                  'LTP_c', 'Prem_c', '%_c', 'Br-Ev_c', 'STRIKE', 'Br-Ev_p',
                  '%_p', 'Prem_p', 'LTP_p'
              ],
                                     **{
                                         'width': 'auto'
                                     }).set_properties(subset=[
                                         'openInterest_c', 'CHNG_OI_c',
                                         'VOLUME_c', 'VOLUME_p', 'CHNG_OI_p',
                                         'openInterest_p'
                                     ],
                                                       **{'width': '250px'})

  html = styler.to_html(index=False)
  return html
