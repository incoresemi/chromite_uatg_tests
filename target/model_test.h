#define MSIP_ADDR 0x2000000
#define SSIP_ADDR 0x2000000
#define MTIMECMP_ADDR 0x200bff8
#define MTIME_ADDR 0x2004000

#define RVMODEL_DATA_SECTION                                \
  .pushsection .tohost,"aw",@progbits;                      \
  .align 8; .global tohost; tohost: .dword 0;               \
  .align 8; .global fromhost; fromhost: .dword 0;           \
  .popsection;                                              \
  .align 8; .global begin_regstate; begin_regstate:         \
  .word 128;                                                \
  .align 8; .global end_regstate; end_regstate:             \
  .word 4;

//RV_COMPLIANCE_HALT
#define RVMODEL_HALT                                        \
  shakti_end:                                               \
  li gp, 1;                                                 \
  sw gp, tohost, t5;                                        \
  fence.i;                                                  \
  li t6, 0x20000;                                           \
  la t5, begin_signature;                                   \
  sw t5, 0(t6);                                             \
  la t5, end_signature;                                     \
  sw t5, 8(t6);                                             \
  sw t5, 12(t6);  

#define RVMODEL_BOOT

//RV_COMPLIANCE_DATA_BEGIN
#define RVMODEL_DATA_BEGIN                                  \
  RVMODEL_DATA_SECTION                                      \
  .align 4; .global begin_signature; begin_signature:

//RV_COMPLIANCE_DATA_END
#define RVMODEL_DATA_END                                    \
  .align 4; .global end_signature; end_signature:  

//RVTEST_IO_INIT
#define RVMODEL_IO_INIT
//RVTEST_IO_WRITE_STR
#define RVMODEL_IO_WRITE_STR(_R, _STR)
//RVTEST_IO_CHECK
#define RVMODEL_IO_CHECK()
//RVTEST_IO_ASSERT_GPR_EQ
#define RVMODEL_IO_ASSERT_GPR_EQ(_S, _R, _I)
//RVTEST_IO_ASSERT_SFPR_EQ
#define RVMODEL_IO_ASSERT_SFPR_EQ(_F, _R, _I)
//RVTEST_IO_ASSERT_DFPR_EQ
#define RVMODEL_IO_ASSERT_DFPR_EQ(_D, _R, _I)

#define RVMODEL_SET_MSW_INT                                 \
  li t1, 1;                                                 \
  li t2, MSIP_ADDR;                                         \
  sb t1, 0(t2);

#define RVMODEL_CLEAR_MSW_INT                               \
  li t2, MSIP_ADDR;                                         \
  sb x0, 0(t2);

#define RVMODEL_SET_MTIMER_INT                              \
  li t1, MTIME_ADDR;                                        \
  li t2, MTIMECMP_ADDR;                                     \
  ld t3, 0(t2);                                             \
  addi t3, t3, -1;                                          \
  sd t3, 0(t1);
                               //     mtimecmp          mtime
#define RVMODEL_CLEAR_MTIMER_INT                            \
  li t1, MTIME_ADDR ;                                       \
  li t2, MTIMECMP_ADDR ;                                    \
  ld t3, 0(t2);                                             \
  sd t3, 0(t1);

#define RVMODEL_SET_SSW_INT                                 \
  li t1, 1;                                                 \
  li t2, SSIP_ADDR;                                         \
  sb t1, 0(t2);

#define RVMODEL_CLEAR_SSW_INT                               \
  li t2, SSIP_ADDR;                                         \
  sb x0, 0(t2);

#define RVMODEL_CLEAR_MEXT_INT
