
#ifndef Utils_H
#define Utils_H

namespace liblathe
{

    class Utils
    {
    public:
        // Create a numeric utility helper //
        Utils();
        // Destroy the numeric utility helper //
        ~Utils();

        static float roundoff(float value, int prec)
        {
            // Round a value to the requested number of decimal places //
            float pow_10 = pow(10, prec);
            return round(value * pow_10) / pow_10;
        }

        static bool compareFloats(float A, float B, float prec = 0.1)
        {
            // Test whether the absolute difference is strictly below the supplied tolerance //
            return (fabs(A - B) < prec);
        }
    };

}

#endif
