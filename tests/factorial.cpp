int factorial(int n){
    int res,i;
    res=1;
    for(i=2;i<=n;i++){
        res=res*i;
    }
    return res;
}
int main(){
    int a,i;
    cin>>a;
    i = factorial(a);
    cout<<i;
    return 0;
}
