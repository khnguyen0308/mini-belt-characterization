#ifndef GOERTZEL_H
#define GOERTZEL_H

#include <math.h>
#define pi M_PI

typedef struct {
	float y, d1, d2;
	float f,Fs;
	float reCoeff, imCoeff, aCoeff;
	float R,X;
} goertzel_struct;

typedef struct {
	float M, Phi;

} goertzel_struct_singlesideres;

void goertzel_init2(int k, int N, goertzel_struct* g);

void goertzel_init(double f, double Fs, goertzel_struct* g);

void goertzel(goertzel_struct* g, float x);


void goertzel_end(goertzel_struct* g, goertzel_struct_singlesideres* g1, int N) ;

#endif
