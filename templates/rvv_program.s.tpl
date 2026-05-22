# Generated RVV profiling experiment.
# experiment_id: $experiment_id
# template_id: $template_id
# vector_shape: e$sew,$lmul
# markers: $marker_summary
#
# Timestamp markers are emitted as zero-cost labels at the next instruction PC.
# experiment.yaml records the corresponding global symbols and marker semantics.

    .section .text
    .globl _start
_start:
$setup_block

$body_block

    # Terminate through the conventional Linux exit syscall for runners that
    # execute the assembled program directly.
    li a0, 0
    li a7, 93
    ecall
$data_block
