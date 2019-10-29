# vapoursynth-tonemapping

Conversion from HDR (matrix=2020, primaries=2020) to full HD SDR (matrix=709, primaries=709)

## Functions:  
- bt2390_ictcp : tonemapping in ICtCp color space, the tonemapping operator used is bt2390 
- reinhard_xyy : tonemapping in xyY color space, the tonemapping operator used is Reinhard extended

- reinhard_yuv : tonemapping in YCbCr color space, the tonemapping operator used is Reinhard extended

- reinhard_rgby : tonemapping in RGB+Y color space, the tonemapping operator used is Reinhard extended



## BASIC USAGE

> import age_tm

> import vapoursynth as vs

> c = core.ffms2.Source(source = '...')

> c=age_tm.reinhard_rgby(c,target_nits=100,source_peak=None)

> c.set_output()


## formulas used

- Reinhard extended 
It maps the max HDR value to 1

Y = (((x / (max_value * max_value)) + 1) * x ) /  ( x + 1)

- RGBY modify luminance

Y = (RGB / luminance_hdr) * luminance_tonemapped

- RGBY modify saturation

Y =  (RGB - luminance) * saturation + luminance


## considerations

All the functions in the script have a common "dynamic" desaturation, it's a "luminosity mask" based on the HDR luminance value,
it maps the target_peak to 0 and the source_peak to 0.5, leaving untouched the saturation under the target_peak and recovering half saturation and half 
luminance in the highlights.
The resulting tonemapped clip is merged at 50% with an rgb tonemapped clip.

That's all for xyY  and RGBY color spaces as they present some kind of auto-desaturation.

ICtCp and YCbCr need two other steps  for the correct desaturation.
 











