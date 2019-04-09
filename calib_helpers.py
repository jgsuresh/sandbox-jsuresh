def LL_compression(LL):
    # Mapping from real numbers to [0,1] which compresses possible range of LL values.

    def LL_compression_sigmoid(x,x0=-30,x1=-2,y0=0.1,y1=0.9):
        g = np.log(y1/y0)
        a = 2*g/(x1-x0)
        b = -g*(x0+x1)/(x1-x0)

        return np.exp(a*x+b)/(np.exp(a*x+b)+1)

    return LL_compression_sigmoid(LL)
