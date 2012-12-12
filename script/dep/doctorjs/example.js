var a1 = ["this is the first element", "this is the second element"];
var a2 = new Array("this is the first element", "this is the second element");
var a3 = new Array();

var b1 = new Boolean(false);
var b2 = false;
var b3 = Boolean(false); 

var d1 = new Date();
var d2 = new Date(300);
var d3 = new Date("10/12/1989")
var d4 = new Date(1989, 2, 10, 10, 20, 59, 45);

var biggestNum = Number.MAX_VALUE;
var smallestNum = Number.MIN_VALUE;
var infiniteNum = Number.POSITIVE_INFINITY;
var negInfiniteNum = Number.NEGATIVE_INFINITY;
var notANum = Number.NaN;
var dateToNumber = Number(d1);
var n1 = new Number(2);
var n2 = 4;

var o1 = function () {
  this.n = 1;
};

o1.prototype.fun = function () {};

var inst = new o1();

var o2 = {
  prop1: 10,
  prop2: [10, 12],
  prop3: 'prop3',
  prop4: {
    prop41: 10
  }
}

var r1 = new RegExp("\\w+");
var r2 = /\w+/;
var r3 = new RegExp("ab+c", "i");

var s1 = String('s');
var s2 = String("s");
var s3 = new String("s");
var s4 = new String('s');
var s5 = 's';
var s6 = "s";

var f1 = function (arg1, agr2) {
  return a1;
};

function f2 (arg1, arg2) {
  return b1;
};

var f3 = function (arg1, agr2) {
  return d1;
};

function f4 (arg1, arg2) {
  return n1;
};

function f5 (arg1, arg2) {
  return o1;
};

function f6 (arg1, arg2) {
  return inst;
};

function f7 (arg1, arg2) {
  return o2;
};

function f8 (arg1, arg2) {
  return r1;
};

function f9 (arg1, arg2) {
  return s1;
};