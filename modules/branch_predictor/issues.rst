===============================================
List of known issues with Gshare FA BPU Testing
===============================================

Open issues
===========
- The hashing function is not easily predictable, hence it is not possible to create tests which require the BHT index to be fixed, say predict-mispredict test. 
  
  :Tests dependent on this issue:
  * **Predict-Mispredict test:** This test predicts a branch to be taken and not 
    taken correctly. Currently, the BPU gets trained to predict taken correctly, 
    but when attempting to correctly predict a not taken, the BHT index changes.
    This makes the BPU predict not taken, which is correct, but this is not what
    we require for the test to pass.
  * **Cheking if 'ALL' BHT entries are updated properly:** This test checks if all
    the BHT entries get updated properly (as shown in the FSM). Currently, the 
    intractability of the BHT updation makes it difficult to perform this test. 

Closed issues
=============
