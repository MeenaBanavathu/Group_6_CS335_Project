int fib(int n){
    //base case
    if(n==0 || n==1){
        return 1;
    }
    return n;
}
int main(){
    int n,i;
    cin>>n;
    i=fib(n);
    cout<<i;
    return 0;
}
