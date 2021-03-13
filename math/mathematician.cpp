#include "mathematician.h"

Mathematician::Mathematician(){
    m_count = 0;
}

Mathematician::~Mathematician() {

}

int Mathematician::inc() {
    m_count ++;
    return m_count;
}