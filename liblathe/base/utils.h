
#ifndef Utils_H
#define Utils_H

class Utils
{
    public:
        Utils();
        ~Utils();

        static float roundoff(float value, int prec){
            float pow_10 = pow(10, prec);
            return round(value * pow_10) / pow_10;
        }

};

#endif