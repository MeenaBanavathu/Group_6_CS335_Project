int gcd(int n, int m){
    int temp;
    while(m!=0){
        temp = m;
        m = n%m;
        n = temp;
    }
    return n;
}
int main(){
    int n,m,i;
    cin>>n;
    cin>>m;
    i = gcd(n,m);
    cout<<i;
}
