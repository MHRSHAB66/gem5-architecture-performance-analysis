/*
 * matrix_tiled.c - Tiled (blocked) matrix multiplication
 * ACA Project 3 - Part 1 (Step 0 / Algorithm 2)
 *
 * Identical input data to matrix_naive.c (same srand(1) / rand()%10
 * generation order), identical checksum output.
 *
 * Tile size T defaults to 32 and can be overridden with argv[1].
 * Rationale for T=32: with 4-byte int elements, three 32x32 tiles
 * (one each of A, B, C) occupy 3 * 32*32 * 4 = 12 KiB, which fits
 * comfortably in a 32 KiB L1 data cache.
 *
 * Tail blocks (dimensions not divisible by T) are handled by the
 * min(I+T, n) bounds. C is zero-initialised (static storage) and
 * updated with += per K-block, matching the assignment pseudocode.
 */

#include <stdio.h>
#include <stdlib.h>

#define N 100 /* rows of A / rows of C  */
#define M 100 /* cols of A / rows of B  */
#define P 100 /* cols of B / cols of C  */

#define DEFAULT_TILE 32

static int A[N][M];
static int B[M][P];
static int C[N][P]; /* static storage => zero-initialised */

static volatile long long g_sink;

static inline int imin(int a, int b) { return a < b ? a : b; }

static void init_matrices(void)
{
    srand(1); /* identical seed and call order to matrix_naive.c */
    for (int i = 0; i < N; i++)
        for (int j = 0; j < M; j++)
            A[i][j] = rand() % 10;
    for (int i = 0; i < M; i++)
        for (int j = 0; j < P; j++)
            B[i][j] = rand() % 10;
}

int main(int argc, char **argv)
{
    int T = DEFAULT_TILE;
    if (argc > 1) {
        T = atoi(argv[1]);
        if (T <= 0)
            T = DEFAULT_TILE;
    }

    init_matrices();

    /* Algorithm 2: tiled matrix multiplication with tail handling */
    for (int I = 0; I < N; I += T) {
        for (int J = 0; J < P; J += T) {
            for (int K = 0; K < M; K += T) {
                const int imax = imin(I + T, N);
                const int jmax = imin(J + T, P);
                const int kmax = imin(K + T, M);
                for (int i = I; i < imax; i++) {
                    for (int j = J; j < jmax; j++) {
                        int sum = 0;
                        for (int k = K; k < kmax; k++)
                            sum += A[i][k] * B[k][j];
                        C[i][j] += sum;
                    }
                }
            }
        }
    }

    long long checksum = 0;
    for (int i = 0; i < N; i++)
        for (int j = 0; j < P; j++)
            checksum += C[i][j];
    g_sink = checksum;

    printf("MATRIX_CHECKSUM: %lld\n", (long long)g_sink);
    printf("MATRIX_DONE: tiled %dx%dx%d T=%d\n", N, M, P, T);
    return 0;
}
