/* Re-implement some methods IE sadly does not */

if(typeof(Array.prototype.indexOf) == 'undefined') {
    // indexOf() function prototype for IE6/7/8 compatibility, taken from
    // JavaScript Standard Library - http://www.devpro.it/JSL/
    Array.prototype.indexOf=function(elm,i){
        var j=this.length;
        if(!i)i=0;
        if(i>=0){while(i<j){if(this[i++]===elm){
            i=i-1+j;j=i-j;
        }}}
        else
            j=this.indexOf(elm,j+i);
        return j!==this.length?j:-1;
    }
}

if (!Array.prototype.filter)
{
    Array.prototype.filter = function(fun /*, thisp*/)
    {
        var len = this.length;
        if (typeof fun != "function")
            throw new TypeError();

        var res = new Array();
        var thisp = arguments[1];
        for (var i = 0; i < len; i++)
            {
                if (i in this)
                    {
                        var val = this[i]; // in case fun mutates this
                        if (fun.call(thisp, val, i, this))
                            res.push(val);
                    }
            }

        return res;
    };
}
