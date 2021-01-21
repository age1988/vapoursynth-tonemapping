# vapoursynth-tonemapping

Conversion from HDR (matrix=2020, primaries=2020) to full HD SDR (matrix=709, primaries=709)

## Functions:  
- bt2390_ictcp : tonemapping in ICtCp color space, the tonemapping operator used is bt2390 




## BASIC USAGE

> import age_tm

> import vapoursynth as vs

> c = core.ffms2.Source(source = '...')

> c=age_tm.bt2390_ictcp(c,target_nits=100,source_peak=1000)

> c.set_output()



 











