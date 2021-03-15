#if !defined(MYMATH_H)
#define MYMATH_H

#if defined _WIN32 || defined __CYGWIN__
    #if BINDINGS_BUILD
        #define BINDINGS_API __declspec(dllexport)
    #else
        #define BINDINGS_API __declspec(dllimport)
    #endif
#else
    #define BINDINGS_API
#endif

class BINDINGS_API Mathematician{
public:
    Mathematician();
    ~Mathematician();

    void inc();
    int getCount();

private:
    int m_count = 0;
};

#endif // MYMATH_H