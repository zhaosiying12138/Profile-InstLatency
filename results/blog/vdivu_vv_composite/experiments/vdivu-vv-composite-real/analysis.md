# vdivu.vv Composite Blog Experiment

Mode: real_platform_profile
Backend: gem5_minor

## Marker Deltas

| Segment | Start | End | Delta | Interpretation |
| --- | ---: | ---: | ---: | --- |
| m1_gap2 | 167 | 171 | 4 | Two fillers leave one dependency bubble before the consumer. |
| m1_ind | 318 | 321 | 3 | Four independent m1 divides have issue starts at +0/+1/+2/+3. |
| m1_raw | 482 | 490 | 8 | Three dependent divides have two +4 latency gaps. |
| m2_ind | 657 | 662 | 5 | Three m2 divides occupy two micro cycles each; macro starts are +0/+2/+4. |
| m4_ind | 830 | 837 | 7 | Two m4 divides occupy four micro cycles each; macro starts are +0/+4. |

## Dynamic Rows Used By The Blog

```text
167000: system.cpu: T0 : 0x80000060 @__prof_marker_m1_gap2_start    : vdivu_vv v8, v0, v1
167000: system.cpu: T0 : 0x80000060 @__prof_marker_m1_gap2_start. 0 : vdivu_vv_micro v8, v0, v1  : SimdDiv :  D=[04000000_04000000_04000000_04000000_04000000_04000000_04000000_04000000]
168000: system.cpu: T0 : 0x80000064 @__prof_marker_m1_gap2_start+4    : vadd_vv v9, v0, v1
168000: system.cpu: T0 : 0x80000064 @__prof_marker_m1_gap2_start+4. 0 : vadd_vv_micro v9, v0, v1   : SimdAdd :  D=[0f000000_0f000000_0f000000_0f000000_0f000000_0f000000_0f000000_0f000000]
169000: system.cpu: T0 : 0x80000068 @__prof_marker_m1_gap2_start+8    : vadd_vv v10, v0, v1
169000: system.cpu: T0 : 0x80000068 @__prof_marker_m1_gap2_start+8. 0 : vadd_vv_micro v10, v0, v1  : SimdAdd :  D=[0f000000_0f000000_0f000000_0f000000_0f000000_0f000000_0f000000_0f000000]
171000: system.cpu: T0 : 0x8000006c @__prof_marker_m1_gap2_start+12    : vadd_vv v11, v8, v1
171000: system.cpu: T0 : 0x8000006c @__prof_marker_m1_gap2_start+12. 0 : vadd_vv_micro v11, v8, v1  : SimdAdd :  D=[07000000_07000000_07000000_07000000_07000000_07000000_07000000_07000000]
171000: system.cpu: T0 : 0x80000070 @__prof_marker_m1_gap2_end    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
172000: system.cpu: T0 : 0x80000074 @__prof_marker_m1_gap2_end+4    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
172000: system.cpu: T0 : 0x80000078 @__prof_marker_m1_gap2_end+8    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
173000: system.cpu: T0 : 0x8000007c @__prof_marker_m1_gap2_end+12    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
203000: system.cpu: T0 : 0x80000080 @__prof_marker_m1_gap2_end+16    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
203000: system.cpu: T0 : 0x80000084 @__prof_marker_m1_gap2_end+20    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
204000: system.cpu: T0 : 0x80000088 @__prof_marker_m1_gap2_end+24    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
204000: system.cpu: T0 : 0x8000008c @__prof_marker_m1_gap2_end+28    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
205000: system.cpu: T0 : 0x80000090 @__prof_marker_m1_gap2_end+32    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
205000: system.cpu: T0 : 0x80000094 @__prof_marker_m1_gap2_end+36    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
206000: system.cpu: T0 : 0x80000098 @__prof_marker_m1_gap2_end+40    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
206000: system.cpu: T0 : 0x8000009c @__prof_marker_m1_gap2_end+44    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
207000: system.cpu: T0 : 0x800000a0 @__prof_marker_m1_gap2_end+48    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
207000: system.cpu: T0 : 0x800000a4 @__prof_marker_m1_gap2_end+52    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
208000: system.cpu: T0 : 0x800000a8 @__prof_marker_m1_gap2_end+56    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
208000: system.cpu: T0 : 0x800000ac @__prof_marker_m1_gap2_end+60    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
209000: system.cpu: T0 : 0x800000b0 @__prof_marker_m1_gap2_end+64    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
209000: system.cpu: T0 : 0x800000b4 @__prof_marker_m1_gap2_end+68    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
210000: system.cpu: T0 : 0x800000b8 @__prof_marker_m1_gap2_end+72    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
210000: system.cpu: T0 : 0x800000bc @__prof_marker_m1_gap2_end+76    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
258000: system.cpu: T0 : 0x800000c0 @__prof_marker_m1_gap2_end+80    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
258000: system.cpu: T0 : 0x800000c4 @__prof_marker_m1_gap2_end+84    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
259000: system.cpu: T0 : 0x800000c8 @__prof_marker_m1_gap2_end+88    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
259000: system.cpu: T0 : 0x800000cc @__prof_marker_m1_gap2_end+92    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
260000: system.cpu: T0 : 0x800000d0 @__prof_marker_m1_gap2_end+96    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
260000: system.cpu: T0 : 0x800000d4 @__prof_marker_m1_gap2_end+100    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
261000: system.cpu: T0 : 0x800000d8 @__prof_marker_m1_gap2_end+104    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
261000: system.cpu: T0 : 0x800000dc @__prof_marker_m1_gap2_end+108    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
262000: system.cpu: T0 : 0x800000e0 @__prof_marker_m1_gap2_end+112    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
262000: system.cpu: T0 : 0x800000e4 @__prof_marker_m1_gap2_end+116    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
263000: system.cpu: T0 : 0x800000e8 @__prof_marker_m1_gap2_end+120    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
263000: system.cpu: T0 : 0x800000ec @__prof_marker_m1_gap2_end+124    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
264000: system.cpu: T0 : 0x800000f0 @__prof_marker_m1_gap2_end+128    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
264000: system.cpu: T0 : 0x800000f4 @__prof_marker_m1_gap2_end+132    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
265000: system.cpu: T0 : 0x800000f8 @__prof_marker_m1_gap2_end+136    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
265000: system.cpu: T0 : 0x800000fc @__prof_marker_m1_gap2_end+140    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
313000: system.cpu: T0 : 0x80000100 @__prof_marker_m1_gap2_end+144    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
313000: system.cpu: T0 : 0x80000104 @__prof_marker_m1_gap2_end+148    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
314000: system.cpu: T0 : 0x80000108 @__prof_marker_m1_gap2_end+152    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
314000: system.cpu: T0 : 0x8000010c @__prof_marker_m1_gap2_end+156    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
315000: system.cpu: T0 : 0x80000110 @__prof_marker_m1_gap2_end+160    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
318000: system.cpu: T0 : 0x80000114 @__prof_marker_m1_ind_start    : vdivu_vv v12, v0, v1
318000: system.cpu: T0 : 0x80000114 @__prof_marker_m1_ind_start. 0 : vdivu_vv_micro v12, v0, v1 : SimdDiv :  D=[04000000_04000000_04000000_04000000_04000000_04000000_04000000_04000000]
319000: system.cpu: T0 : 0x80000118 @__prof_marker_m1_ind_start+4    : vdivu_vv v13, v0, v1
319000: system.cpu: T0 : 0x80000118 @__prof_marker_m1_ind_start+4. 0 : vdivu_vv_micro v13, v0, v1 : SimdDiv :  D=[04000000_04000000_04000000_04000000_04000000_04000000_04000000_04000000]
320000: system.cpu: T0 : 0x8000011c @__prof_marker_m1_ind_start+8    : vdivu_vv v14, v0, v1
320000: system.cpu: T0 : 0x8000011c @__prof_marker_m1_ind_start+8. 0 : vdivu_vv_micro v14, v0, v1 : SimdDiv :  D=[04000000_04000000_04000000_04000000_04000000_04000000_04000000_04000000]
321000: system.cpu: T0 : 0x80000120 @__prof_marker_m1_ind_start+12    : vdivu_vv v15, v0, v1
321000: system.cpu: T0 : 0x80000120 @__prof_marker_m1_ind_start+12. 0 : vdivu_vv_micro v15, v0, v1 : SimdDiv :  D=[04000000_04000000_04000000_04000000_04000000_04000000_04000000_04000000]
321000: system.cpu: T0 : 0x80000124 @__prof_marker_m1_ind_end    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
322000: system.cpu: T0 : 0x80000128 @__prof_marker_m1_ind_end+4    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
322000: system.cpu: T0 : 0x8000012c @__prof_marker_m1_ind_end+8    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
323000: system.cpu: T0 : 0x80000130 @__prof_marker_m1_ind_end+12    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
323000: system.cpu: T0 : 0x80000134 @__prof_marker_m1_ind_end+16    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
324000: system.cpu: T0 : 0x80000138 @__prof_marker_m1_ind_end+20    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
324000: system.cpu: T0 : 0x8000013c @__prof_marker_m1_ind_end+24    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
368000: system.cpu: T0 : 0x80000140 @__prof_marker_m1_ind_end+28    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
368000: system.cpu: T0 : 0x80000144 @__prof_marker_m1_ind_end+32    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
369000: system.cpu: T0 : 0x80000148 @__prof_marker_m1_ind_end+36    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
369000: system.cpu: T0 : 0x8000014c @__prof_marker_m1_ind_end+40    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
370000: system.cpu: T0 : 0x80000150 @__prof_marker_m1_ind_end+44    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
370000: system.cpu: T0 : 0x80000154 @__prof_marker_m1_ind_end+48    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
371000: system.cpu: T0 : 0x80000158 @__prof_marker_m1_ind_end+52    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
371000: system.cpu: T0 : 0x8000015c @__prof_marker_m1_ind_end+56    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
372000: system.cpu: T0 : 0x80000160 @__prof_marker_m1_ind_end+60    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
372000: system.cpu: T0 : 0x80000164 @__prof_marker_m1_ind_end+64    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
373000: system.cpu: T0 : 0x80000168 @__prof_marker_m1_ind_end+68    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
373000: system.cpu: T0 : 0x8000016c @__prof_marker_m1_ind_end+72    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
374000: system.cpu: T0 : 0x80000170 @__prof_marker_m1_ind_end+76    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
374000: system.cpu: T0 : 0x80000174 @__prof_marker_m1_ind_end+80    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
375000: system.cpu: T0 : 0x80000178 @__prof_marker_m1_ind_end+84    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
375000: system.cpu: T0 : 0x8000017c @__prof_marker_m1_ind_end+88    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
423000: system.cpu: T0 : 0x80000180 @__prof_marker_m1_ind_end+92    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
423000: system.cpu: T0 : 0x80000184 @__prof_marker_m1_ind_end+96    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
424000: system.cpu: T0 : 0x80000188 @__prof_marker_m1_ind_end+100    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
424000: system.cpu: T0 : 0x8000018c @__prof_marker_m1_ind_end+104    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
425000: system.cpu: T0 : 0x80000190 @__prof_marker_m1_ind_end+108    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
425000: system.cpu: T0 : 0x80000194 @__prof_marker_m1_ind_end+112    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
426000: system.cpu: T0 : 0x80000198 @__prof_marker_m1_ind_end+116    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
426000: system.cpu: T0 : 0x8000019c @__prof_marker_m1_ind_end+120    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
427000: system.cpu: T0 : 0x800001a0 @__prof_marker_m1_ind_end+124    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
427000: system.cpu: T0 : 0x800001a4 @__prof_marker_m1_ind_end+128    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
428000: system.cpu: T0 : 0x800001a8 @__prof_marker_m1_ind_end+132    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
428000: system.cpu: T0 : 0x800001ac @__prof_marker_m1_ind_end+136    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
429000: system.cpu: T0 : 0x800001b0 @__prof_marker_m1_ind_end+140    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
429000: system.cpu: T0 : 0x800001b4 @__prof_marker_m1_ind_end+144    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
430000: system.cpu: T0 : 0x800001b8 @__prof_marker_m1_ind_end+148    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
430000: system.cpu: T0 : 0x800001bc @__prof_marker_m1_ind_end+152    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
478000: system.cpu: T0 : 0x800001c0 @__prof_marker_m1_ind_end+156    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
478000: system.cpu: T0 : 0x800001c4 @__prof_marker_m1_ind_end+160    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
482000: system.cpu: T0 : 0x800001c8 @__prof_marker_m1_raw_start    : vdivu_vv v20, v0, v1
482000: system.cpu: T0 : 0x800001c8 @__prof_marker_m1_raw_start. 0 : vdivu_vv_micro v20, v0, v1 : SimdDiv :  D=[04000000_04000000_04000000_04000000_04000000_04000000_04000000_04000000]
486000: system.cpu: T0 : 0x800001cc @__prof_marker_m1_raw_start+4    : vdivu_vv v20, v20, v1
486000: system.cpu: T0 : 0x800001cc @__prof_marker_m1_raw_start+4. 0 : vdivu_vv_micro v20, v20, v1 : SimdDiv :  D=[01000000_01000000_01000000_01000000_01000000_01000000_01000000_01000000]
490000: system.cpu: T0 : 0x800001d0 @__prof_marker_m1_raw_start+8    : vdivu_vv v20, v20, v1
490000: system.cpu: T0 : 0x800001d0 @__prof_marker_m1_raw_start+8. 0 : vdivu_vv_micro v20, v20, v1 : SimdDiv :  D=[00000000_00000000_00000000_00000000_00000000_00000000_00000000_00000000]
490000: system.cpu: T0 : 0x800001d4 @__prof_marker_m1_raw_end    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
491000: system.cpu: T0 : 0x800001d8 @__prof_marker_m1_raw_end+4    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
491000: system.cpu: T0 : 0x800001dc @__prof_marker_m1_raw_end+8    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
492000: system.cpu: T0 : 0x800001e0 @__prof_marker_m1_raw_end+12    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
492000: system.cpu: T0 : 0x800001e4 @__prof_marker_m1_raw_end+16    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
493000: system.cpu: T0 : 0x800001e8 @__prof_marker_m1_raw_end+20    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
493000: system.cpu: T0 : 0x800001ec @__prof_marker_m1_raw_end+24    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
494000: system.cpu: T0 : 0x800001f0 @__prof_marker_m1_raw_end+28    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
494000: system.cpu: T0 : 0x800001f4 @__prof_marker_m1_raw_end+32    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
495000: system.cpu: T0 : 0x800001f8 @__prof_marker_m1_raw_end+36    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
495000: system.cpu: T0 : 0x800001fc @__prof_marker_m1_raw_end+40    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
533000: system.cpu: T0 : 0x80000200 @__prof_marker_m1_raw_end+44    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
533000: system.cpu: T0 : 0x80000204 @__prof_marker_m1_raw_end+48    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
534000: system.cpu: T0 : 0x80000208 @__prof_marker_m1_raw_end+52    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
534000: system.cpu: T0 : 0x8000020c @__prof_marker_m1_raw_end+56    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
535000: system.cpu: T0 : 0x80000210 @__prof_marker_m1_raw_end+60    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
535000: system.cpu: T0 : 0x80000214 @__prof_marker_m1_raw_end+64    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
536000: system.cpu: T0 : 0x80000218 @__prof_marker_m1_raw_end+68    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
536000: system.cpu: T0 : 0x8000021c @__prof_marker_m1_raw_end+72    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
537000: system.cpu: T0 : 0x80000220 @__prof_marker_m1_raw_end+76    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
537000: system.cpu: T0 : 0x80000224 @__prof_marker_m1_raw_end+80    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
538000: system.cpu: T0 : 0x80000228 @__prof_marker_m1_raw_end+84    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
538000: system.cpu: T0 : 0x8000022c @__prof_marker_m1_raw_end+88    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
539000: system.cpu: T0 : 0x80000230 @__prof_marker_m1_raw_end+92    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
539000: system.cpu: T0 : 0x80000234 @__prof_marker_m1_raw_end+96    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
540000: system.cpu: T0 : 0x80000238 @__prof_marker_m1_raw_end+100    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
540000: system.cpu: T0 : 0x8000023c @__prof_marker_m1_raw_end+104    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
588000: system.cpu: T0 : 0x80000240 @__prof_marker_m1_raw_end+108    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
588000: system.cpu: T0 : 0x80000244 @__prof_marker_m1_raw_end+112    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
589000: system.cpu: T0 : 0x80000248 @__prof_marker_m1_raw_end+116    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
589000: system.cpu: T0 : 0x8000024c @__prof_marker_m1_raw_end+120    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
590000: system.cpu: T0 : 0x80000250 @__prof_marker_m1_raw_end+124    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
590000: system.cpu: T0 : 0x80000254 @__prof_marker_m1_raw_end+128    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
591000: system.cpu: T0 : 0x80000258 @__prof_marker_m1_raw_end+132    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
591000: system.cpu: T0 : 0x8000025c @__prof_marker_m1_raw_end+136    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
592000: system.cpu: T0 : 0x80000260 @__prof_marker_m1_raw_end+140    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
592000: system.cpu: T0 : 0x80000264 @__prof_marker_m1_raw_end+144    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
593000: system.cpu: T0 : 0x80000268 @__prof_marker_m1_raw_end+148    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
593000: system.cpu: T0 : 0x8000026c @__prof_marker_m1_raw_end+152    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
594000: system.cpu: T0 : 0x80000270 @__prof_marker_m1_raw_end+156    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
594000: system.cpu: T0 : 0x80000274 @__prof_marker_m1_raw_end+160    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
598000: system.cpu: T0 : 0x80000278 @__prof_marker_m1_raw_end+164    : vsetvli zero, t0, e32, m2, ta, ma : SimdConfig :  D=0x0000000000000010
657000: system.cpu: T0 : 0x80000284 @__prof_marker_m2_ind_start    : vdivu_vv v8, v4, v6
657000: system.cpu: T0 : 0x80000284 @__prof_marker_m2_ind_start. 0 : vdivu_vv_micro v8, v4, v6  : SimdDiv :  D=[04000000_04000000_04000000_04000000_04000000_04000000_04000000_04000000]
658000: system.cpu: T0 : 0x80000284 @__prof_marker_m2_ind_start. 1 : vdivu_vv_micro v9, v5, v7  : SimdDiv :  D=[04000000_04000000_04000000_04000000_04000000_04000000_04000000_04000000]
659000: system.cpu: T0 : 0x80000288 @__prof_marker_m2_ind_start+4    : vdivu_vv v10, v4, v6
659000: system.cpu: T0 : 0x80000288 @__prof_marker_m2_ind_start+4. 0 : vdivu_vv_micro v10, v4, v6 : SimdDiv :  D=[04000000_04000000_04000000_04000000_04000000_04000000_04000000_04000000]
660000: system.cpu: T0 : 0x80000288 @__prof_marker_m2_ind_start+4. 1 : vdivu_vv_micro v11, v5, v7 : SimdDiv :  D=[04000000_04000000_04000000_04000000_04000000_04000000_04000000_04000000]
661000: system.cpu: T0 : 0x8000028c @__prof_marker_m2_ind_start+8    : vdivu_vv v12, v4, v6
661000: system.cpu: T0 : 0x8000028c @__prof_marker_m2_ind_start+8. 0 : vdivu_vv_micro v12, v4, v6 : SimdDiv :  D=[04000000_04000000_04000000_04000000_04000000_04000000_04000000_04000000]
662000: system.cpu: T0 : 0x8000028c @__prof_marker_m2_ind_start+8. 1 : vdivu_vv_micro v13, v5, v7 : SimdDiv :  D=[04000000_04000000_04000000_04000000_04000000_04000000_04000000_04000000]
662000: system.cpu: T0 : 0x80000290 @__prof_marker_m2_ind_end    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
663000: system.cpu: T0 : 0x80000294 @__prof_marker_m2_ind_end+4    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
663000: system.cpu: T0 : 0x80000298 @__prof_marker_m2_ind_end+8    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
664000: system.cpu: T0 : 0x8000029c @__prof_marker_m2_ind_end+12    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
664000: system.cpu: T0 : 0x800002a0 @__prof_marker_m2_ind_end+16    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
665000: system.cpu: T0 : 0x800002a4 @__prof_marker_m2_ind_end+20    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
665000: system.cpu: T0 : 0x800002a8 @__prof_marker_m2_ind_end+24    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
666000: system.cpu: T0 : 0x800002ac @__prof_marker_m2_ind_end+28    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
666000: system.cpu: T0 : 0x800002b0 @__prof_marker_m2_ind_end+32    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
667000: system.cpu: T0 : 0x800002b4 @__prof_marker_m2_ind_end+36    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
667000: system.cpu: T0 : 0x800002b8 @__prof_marker_m2_ind_end+40    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
668000: system.cpu: T0 : 0x800002bc @__prof_marker_m2_ind_end+44    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
705000: system.cpu: T0 : 0x800002c0 @__prof_marker_m2_ind_end+48    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
705000: system.cpu: T0 : 0x800002c4 @__prof_marker_m2_ind_end+52    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
706000: system.cpu: T0 : 0x800002c8 @__prof_marker_m2_ind_end+56    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
706000: system.cpu: T0 : 0x800002cc @__prof_marker_m2_ind_end+60    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
707000: system.cpu: T0 : 0x800002d0 @__prof_marker_m2_ind_end+64    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
707000: system.cpu: T0 : 0x800002d4 @__prof_marker_m2_ind_end+68    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
708000: system.cpu: T0 : 0x800002d8 @__prof_marker_m2_ind_end+72    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
708000: system.cpu: T0 : 0x800002dc @__prof_marker_m2_ind_end+76    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
709000: system.cpu: T0 : 0x800002e0 @__prof_marker_m2_ind_end+80    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
709000: system.cpu: T0 : 0x800002e4 @__prof_marker_m2_ind_end+84    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
710000: system.cpu: T0 : 0x800002e8 @__prof_marker_m2_ind_end+88    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
710000: system.cpu: T0 : 0x800002ec @__prof_marker_m2_ind_end+92    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
711000: system.cpu: T0 : 0x800002f0 @__prof_marker_m2_ind_end+96    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
711000: system.cpu: T0 : 0x800002f4 @__prof_marker_m2_ind_end+100    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
712000: system.cpu: T0 : 0x800002f8 @__prof_marker_m2_ind_end+104    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
712000: system.cpu: T0 : 0x800002fc @__prof_marker_m2_ind_end+108    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
760000: system.cpu: T0 : 0x80000300 @__prof_marker_m2_ind_end+112    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
760000: system.cpu: T0 : 0x80000304 @__prof_marker_m2_ind_end+116    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
761000: system.cpu: T0 : 0x80000308 @__prof_marker_m2_ind_end+120    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
761000: system.cpu: T0 : 0x8000030c @__prof_marker_m2_ind_end+124    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
762000: system.cpu: T0 : 0x80000310 @__prof_marker_m2_ind_end+128    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
762000: system.cpu: T0 : 0x80000314 @__prof_marker_m2_ind_end+132    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
763000: system.cpu: T0 : 0x80000318 @__prof_marker_m2_ind_end+136    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
763000: system.cpu: T0 : 0x8000031c @__prof_marker_m2_ind_end+140    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
764000: system.cpu: T0 : 0x80000320 @__prof_marker_m2_ind_end+144    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
764000: system.cpu: T0 : 0x80000324 @__prof_marker_m2_ind_end+148    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
765000: system.cpu: T0 : 0x80000328 @__prof_marker_m2_ind_end+152    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
765000: system.cpu: T0 : 0x8000032c @__prof_marker_m2_ind_end+156    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
766000: system.cpu: T0 : 0x80000330 @__prof_marker_m2_ind_end+160    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
769000: system.cpu: T0 : 0x80000334 @__prof_marker_m2_ind_end+164    : vsetvli zero, t0, e32, m4, ta, ma : SimdConfig :  D=0x0000000000000020
830000: system.cpu: T0 : 0x80000340 @__prof_marker_m4_ind_start    : vdivu_vv v24, v16, v20
830000: system.cpu: T0 : 0x80000340 @__prof_marker_m4_ind_start. 0 : vdivu_vv_micro v24, v16, v20 : SimdDiv :  D=[04000000_04000000_04000000_04000000_04000000_04000000_04000000_04000000]
831000: system.cpu: T0 : 0x80000340 @__prof_marker_m4_ind_start. 1 : vdivu_vv_micro v25, v17, v21 : SimdDiv :  D=[04000000_04000000_04000000_04000000_04000000_04000000_04000000_04000000]
832000: system.cpu: T0 : 0x80000340 @__prof_marker_m4_ind_start. 2 : vdivu_vv_micro v26, v18, v22 : SimdDiv :  D=[04000000_04000000_04000000_04000000_04000000_04000000_04000000_04000000]
833000: system.cpu: T0 : 0x80000340 @__prof_marker_m4_ind_start. 3 : vdivu_vv_micro v27, v19, v23 : SimdDiv :  D=[04000000_04000000_04000000_04000000_04000000_04000000_04000000_04000000]
834000: system.cpu: T0 : 0x80000344 @__prof_marker_m4_ind_start+4    : vdivu_vv v28, v16, v20
834000: system.cpu: T0 : 0x80000344 @__prof_marker_m4_ind_start+4. 0 : vdivu_vv_micro v28, v16, v20 : SimdDiv :  D=[04000000_04000000_04000000_04000000_04000000_04000000_04000000_04000000]
835000: system.cpu: T0 : 0x80000344 @__prof_marker_m4_ind_start+4. 1 : vdivu_vv_micro v29, v17, v21 : SimdDiv :  D=[04000000_04000000_04000000_04000000_04000000_04000000_04000000_04000000]
836000: system.cpu: T0 : 0x80000344 @__prof_marker_m4_ind_start+4. 2 : vdivu_vv_micro v30, v18, v22 : SimdDiv :  D=[04000000_04000000_04000000_04000000_04000000_04000000_04000000_04000000]
837000: system.cpu: T0 : 0x80000344 @__prof_marker_m4_ind_start+4. 3 : vdivu_vv_micro v31, v19, v23 : SimdDiv :  D=[04000000_04000000_04000000_04000000_04000000_04000000_04000000_04000000]
837000: system.cpu: T0 : 0x80000348 @__prof_marker_m4_ind_end    : addi zero, zero, 0         : IntAlu :  D=0x0000000000000000
838000: system.cpu: T0 : 0x8000034c @__prof_marker_overall_end    : addi a0, zero, 0           : IntAlu :  D=0x0000000000000000
838000: system.cpu: T0 : 0x80000350 @__prof_marker_overall_end+4    : addi a7, zero, 93          : IntAlu :  D=0x000000000000005d
839000: system.cpu: T0 : 0x80000354 @__prof_marker_overall_end+8    : ecall                      : No_OpClass :
```
