# Generated RVV experiment scaffold.
# experiment_id: $experiment_id
# template_id: $template_id
# vector_shape: e$sew,$lmul
# markers: $marker_summary
#
# TIMESTAMP_MARK is a runner/simulator pseudo line. These files document the
# intended experiment shape and are not required to assemble before the marker
# path exists.

    .section .text
    .globl _start
_start:
$setup_block

$body_block

    # Terminate through the conventional Linux exit syscall when a runner
    # chooses to assemble this after marker lowering is implemented.
    li a0, 0
    li a7, 93
    ecall
$data_block
