These tests focus on the incremental hash logic.

General test setup with test directory A:
- Copy A' of A is created.
- Cashier is run on A
- Mutation is performed on both A and A'
- Cashier is rerun on A
- Cashier is run on A'
- Compare results
