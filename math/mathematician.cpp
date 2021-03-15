#include "mathematician.h"

Mathematician::Mathematician(){
    m_count = 0;
}

Mathematician::~Mathematician() {

}

void Mathematician::inc() {
    m_count ++;
}

int Mathematician::getCount() {
    return m_count;
}