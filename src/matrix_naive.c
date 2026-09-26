/*
 * matrix_naive.c - Naive matrix multiplication (i-j-k loop order)
 * ACA Project 3 - Part 1 (Step 0 / Algorithm 1)
 *
 * C = A * B for 100x100 row-major int matrices.
 * Data is generated with rand() after srand(1) so that both the naive
 * and the tiled implementation operate on the exact same matrices and
 * must therefore print the exact same checksum.
 *
 * A checksum over the full output matrix is accumulated into a volatile
 * sink and printed, so the compiler cannot dead-code-eliminate the
 * multiplication at -O2.
 */

#include <stdio.h>
#include <stdlib.h>

#define N 100 /* rows of A / rows of C  */
#define M 100 /* cols of A / rows of B  */
#define P 100 /* cols of B / cols of C  */

static int A[N][M];
static int B[M][P];
static int C[N][P];

/* volatile sink: forces the checksum (and hence the whole computation)
 * to be observable, preventing dead-code elimination. */
static volatile long long g_sink;

static void init_matrices(void)
{
    srand(1); /* fixed seed => fully reproducible input data */
    for (int i = 0; i < N; i++)
        for (int j = 0; j < M; j++)
            A[i][j] = rand() % 10; /* small values: no overflow */
    for (int i = 0; i < M; i++)
        for (int j = 0; j < P; j++)
            B[i][j] = rand() % 10;
}

int main(void)
{
    init_matrices();

    /* Algorithm 1: naive i-j-k matrix multiplication */
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < P; j++) {
            int sum = 0;
            for (int k = 0; k < M; k++)
                sum += A[i][k] * B[k][j];
            C[i][j] = sum;
        }
    }

    long long checksum = 0;
    for (int i = 0; i < N; i++)
        for (int j = 0; j < P; j++)
            checksum += C[i][j];
    g_sink = checksum;

    printf("MATRIX_CHECKSUM: %lld\n", (long long)g_sink);
    printf("MATRIX_DONE: naive %dx%dx%d\n", N, M, P);
    return 0;
}
