interface Student{
    age:number,
    college:string
}

function whether_in_iit_ropar(student:Student):boolean{
    return student.college=="IIT ROPAR"
}

let harkirat:Student={
    age:24,
    college:"IIT ROORKEE"
}

console.log(whether_in_iit_ropar(harkirat))